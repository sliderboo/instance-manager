from repository import RedisStorage
from repository.user import UserRepository
from repository.schema import User
from models.user import QueryUserModel
from fastapi import Depends, HTTPException, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Tuple, Annotated, Union
from hashlib import sha256, pbkdf2_hmac
from hmac import new
from base64 import urlsafe_b64encode, urlsafe_b64decode
from json import dumps, loads
from string import ascii_letters, digits
from random import choices
from redis import Redis
from config import config
import logging

log = logging.getLogger(__name__)


class PasswordHandler:
    @staticmethod
    def hash(password: str) -> str:
        return urlsafe_b64encode(
            pbkdf2_hmac(
                "sha256", password.encode(), config["PASSWORD_SALT"].encode(), 100000
            )
        ).decode()

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        return hashed == PasswordHandler.hash(password)


class Base64:
    @staticmethod
    def encode(data: str) -> str:
        return urlsafe_b64encode(data.encode()).decode().rstrip("=")

    @staticmethod
    def decode(data: str) -> str:
        if not data:
            return ""
        enc = data + "=" * (-len(data) % 4)
        return urlsafe_b64decode(enc.encode()).decode()


class JWTHandler:
    def __init__(self, store: Redis = Depends(RedisStorage.get)):
        self._store = store

    def verify(self, token: str) -> Tuple[Optional[dict], Exception]:
        _, payload, signature = token.split(".")
        try:
            payload = loads(Base64.decode(payload))
            uid = payload.get("uid", None)
            if not uid:
                raise Exception("Invalid payload")
            secret = self._store.get(uid)
            if not secret:
                raise Exception("Invalid or expired token")
            if isinstance(secret, bytes):
                secret = secret.decode()
            if signature != self.sign(payload, secret):
                raise Exception("Invalid signature")
            return payload, None
        except Exception as e:
            return None, Exception(str(e))

    def create(self, payload: dict) -> str:
        try:
            secret = "".join(choices(ascii_letters + digits, k=64))
            uid = payload.get("uid", None)
            if not uid:
                raise Exception("Invalid payload")
            self._store.set(uid, secret, ex=config["JWT_EXPIRATION"])
            return ".".join(
                [
                    Base64.encode(dumps({"alg": "HS256", "typ": "JWT"})),
                    Base64.encode(dumps(payload)),
                    self.sign(payload, secret),
                ]
            )
        except Exception as e:
            return None

    def revoke(self, uid: str) -> None:
        self._store.delete(uid)

    @staticmethod
    def sign(payload: dict, secret: str) -> str:
        payload = dumps({"alg": "HS256", "typ": "JWT"}) + "." + dumps(payload)
        return Base64.encode(new(secret.encode(), payload.encode(), sha256).hexdigest())


def get_cookie_token(
    token: Annotated[Union[None, str], Cookie(alias="auth")] = None
) -> Optional[str]:
    return token


def auth(
    request: Request,
    *,
    strict: bool = False,
    jwt_handler: JWTHandler = Depends(JWTHandler),
    user_repo: UserRepository = Depends(UserRepository),
    token: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    cookie_token: str = Depends(get_cookie_token),
):
    log.debug(f"{request.headers}")
    cred = None
    if not token:
        cred = cookie_token
    else:
        cred = token.credentials
    if not cred:
        if strict:
            raise HTTPException(status_code=403, detail="Please login first")
        return None
    try:
        if cred == config["BOT_TOKEN"]:
            return User(id="bot", email="bot@game")
        payload, _ = jwt_handler.verify(cred)
        if not payload:
            return None
        exist_user = user_repo.find_one(
            query=QueryUserModel(id=payload.get("uid", None))
        )
        if strict and not exist_user:
            raise Exception("Please login first")
        log.debug(
            "request from user: {}".format(
                exist_user.display_name if exist_user else "Guest"
            )
        )
        return exist_user
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
