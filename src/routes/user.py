from fastapi import APIRouter, status, Depends

from models.dto.user import UserResponseModel, UserResponse
from repository.schema import User

from utils.api import APIResponse
from utils.gate_keeper import auth

router = APIRouter()


@router.get("/me", tags=["user"], response_model=UserResponseModel)
async def me(user: User = Depends(auth)):
    return APIResponse.as_json(
        code=status.HTTP_200_OK,
        status="success",
        data=UserResponse.model_validate(user, from_attributes=True).model_dump(),
    )
