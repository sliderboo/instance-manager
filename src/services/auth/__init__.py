from repository.user import UserRepository

from models.dto.user import NewUserRequest, UserResponse, UserRequest
from models.user import QueryUserModel, UserModel

from utils.gate_keeper import JWTHandler, PasswordHandler
from fastapi import Depends, HTTPException
from uuid import uuid4
from string import ascii_letters, digits
from random import choices
from config import config
from services.auth.protocols import BaseService
from unidecode import unidecode

third_party_module = __import__(
    f"services.auth.protocols.{config['CTF_PLATFORM']}",
    fromlist=[config["CTF_PLATFORM"]],
)

Service: BaseService = getattr(third_party_module, "Service")


def normalize(name):
    return unidecode(name)


class AuthService:
    def __init__(
        self,
        repo: UserRepository = Depends(UserRepository),
        jwt_handler: JWTHandler = Depends(JWTHandler),
    ) -> None:
        self._repo = repo
        self._jwt = jwt_handler

    def signup(self, user: NewUserRequest) -> UserResponse:
        try:
            exist_user = self._repo.find_one(query=QueryUserModel(email=user.email))
            assert exist_user is None, "User already exists"
            new_user = UserModel(
                id=str(uuid4()),
                slug=self.gen_slug(user.display_name),
                email=user.email,
                password=PasswordHandler.hash(user.password),
                display_name=user.display_name,
            )
            new_user = self._repo.create(new_user)
            assert new_user is not None, "Failed to create user"
            new_user = UserResponse(
                id=new_user.id,
                slug=new_user.slug,
                email=new_user.email,
                display_name=new_user.display_name,
            )
            return new_user
        except Exception as e:
            raise HTTPException(status_code=204, detail=str(e))

    def signin(self, user: UserRequest) -> str:
        print(f"DEBUG: Login attempt with email='{user.email}' and password='{user.password}'")
        
        # TEST MODE: Allow test credentials for development
        if user.email == "test@example.com" and user.password == "test_token":
            print("DEBUG: Matched test@example.com credentials")
            try:
                # Create or get test user
                exist_user = self._repo.find_one(query=QueryUserModel(email="test@example.com"))
                if not exist_user:
                    print("DEBUG: Creating new test user")
                    exist_user = UserModel(
                        id=str(uuid4()),
                        email="test@example.com",
                        display_name="Test User",
                        is_admin=False,
                    )
                    exist_user = self._repo.create(exist_user)
                    if not exist_user:
                        raise Exception("Failed to create user in database")
                    print(f"DEBUG: User created successfully with ID: {exist_user.id}")
                
                token = self._jwt.create({"uid": exist_user.id})
                if token is None:
                    raise Exception("Failed to create token")
                print("DEBUG: Successfully created token for test user")
                return token
            except Exception as e:
                print("Error when sign in (test user): ", e)
                raise HTTPException(status_code=204, detail=str(e))
        
        # TEST MODE: Allow admin credentials for development
        if user.email == "admin@example.com" and user.password == "admin_token":
            print("DEBUG: Matched admin@example.com credentials")
            try:
                # Create or get admin user
                exist_user = self._repo.find_one(query=QueryUserModel(email="admin@example.com"))
                if not exist_user:
                    print("DEBUG: Creating new admin user")
                    exist_user = UserModel(
                        id=str(uuid4()),
                        email="admin@example.com",
                        display_name="Admin User",
                        is_admin=True,
                    )
                    exist_user = self._repo.create(exist_user)
                    if not exist_user:
                        raise Exception("Failed to create admin user in database")
                    print(f"DEBUG: Admin user created successfully with ID: {exist_user.id}")
                else:
                    print("DEBUG: Found existing admin user")
                
                token = self._jwt.create({"uid": exist_user.id})
                if token is None:
                    raise Exception("Failed to create token")
                print("DEBUG: Successfully created token for admin user")
                return token
            except Exception as e:
                print("Error when sign in (admin user): ", e)
                raise HTTPException(status_code=204, detail=str(e))
        
        print("DEBUG: No test credentials matched, trying CTFd authentication")
        # Original CTFd authentication for other users
        try:
            thirdPartyService = Service()
            user_data = thirdPartyService.fetch_user_info(user.email, user.password)
            if not user_data:
                raise Exception("Failed to fetch user data from CTFd")
            
            print(f"DEBUG: CTFd user data: email={user_data['email']}, name={user_data['name']}")
            
            exist_user = self._repo.find_one(
                query=QueryUserModel(email=user_data["email"])
            )
            
            if not exist_user:
                print(f"DEBUG: User not found in database, creating new user")
                new_user = UserModel(
                    id=str(uuid4()),
                    email=user_data["email"],
                    display_name=normalize(user_data["name"]),
                    is_admin=False,
                )
                exist_user = self._repo.create(new_user)
                
                if not exist_user:
                    # Try to find if user with same display name exists
                    name_conflict = self._repo.find_one(
                        query=QueryUserModel(display_name=normalize(user_data["name"]))
                    )
                    if name_conflict:
                        raise Exception(f"Display name '{normalize(user_data['name'])}' already exists. Please contact admin.")
                    raise Exception("Failed to create user in database. Unknown error.")
                
                print(f"DEBUG: User created successfully with ID: {exist_user.id}")
            else:
                print(f"DEBUG: Found existing user with ID: {exist_user.id}")

            token = self._jwt.create({"uid": exist_user.id})
            if token is None:
                raise Exception("Failed to create token")
            
            print(f"DEBUG: Successfully created token for user {exist_user.email}")
            return token
        except Exception as e:
            print(f"Error when sign in: {e}")
            raise HTTPException(status_code=204, detail=str(e))

    def logout(self, uid: str) -> None:
        try:
            self._jwt.revoke(uid)
        except Exception as e:
            raise HTTPException(status_code=204, detail=str(e))

    @staticmethod
    def gen_slug(display_name: str) -> str:
        return (
            display_name.lower().replace(" ", "-")
            + "-"
            + "".join(choices(ascii_letters + digits, k=6))
        )
