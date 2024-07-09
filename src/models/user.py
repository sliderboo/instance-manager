from pydantic import BaseModel
from typing import Optional


class UserModel(BaseModel):
    id: Optional[str] = None
    email: str
    display_name: str
    is_admin: Optional[bool] = False


class QueryUserModel(BaseModel):
    email: Optional[str] = None
    id: Optional[str] = None
    display_name: Optional[str] = None
