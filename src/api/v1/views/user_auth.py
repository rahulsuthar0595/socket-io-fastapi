from fastapi import APIRouter, HTTPException

from src.api.v1.repository.mongo_core_repository import retrieve_user_by_email, insert_users_detail
from src.api.v1.schema.user_auth import UserRequest, UserBase

router = APIRouter(prefix="/auth")


@router.post("/login")
async def user_login(user_data: UserBase):
    user = await retrieve_user_by_email(user_data.email)
    if user:
        return user
    else:
        raise HTTPException(detail="User not found.", status_code=404)


@router.post("/registration")
async def user_login(user_data: UserRequest):
    user = await retrieve_user_by_email(user_data.email)
    if not user:
        data = user_data.model_dump()
        response = await insert_users_detail(data)
        return response
    else:
        raise HTTPException(detail="User already exists with this email.", status_code=400)
