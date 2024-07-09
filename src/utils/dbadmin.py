from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from fastapi.responses import RedirectResponse
from repository import Storage, RedisStorage
from repository.user import UserRepository
from utils.gate_keeper import auth, JWTHandler


class MyAuth(AuthenticationBackend):
    async def authenticate(self, request: Request):
        is_admin = False
        try:
            storage = next(Storage.get())

            self._user = auth(
                request,
                strict=True,
                jwt_handler=JWTHandler(next(RedisStorage.get())),
                user_repo=UserRepository(storage),
                token=None,
                cookie_token=request.cookies.get("auth"),
            )
            is_admin = self._user.is_admin
        except:
            is_admin = False
        if not is_admin:
            return RedirectResponse("/signin")
        return is_admin
