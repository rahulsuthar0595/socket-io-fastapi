from pydantic import BaseModel, EmailStr



class UserBase(BaseModel):
    email: EmailStr
    password: str


class UserRequest(UserBase):
    full_name: str
    email: EmailStr
    password: str

