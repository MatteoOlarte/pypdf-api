from typing import Annotated

from pydantic import (BaseModel, Field, EmailStr)


class BaseUser(BaseModel):
    email: EmailStr
    first_name: Annotated[str, Field(max_length=255)]
    last_name: Annotated[str, Field(max_length=255)]


class AuthUser(BaseUser):
    password: Annotated[str, Field(min_length=8, examples=['12345678'])]


class PublicUser(BaseUser):
    class Config:
        orm_mode = True

    user_id: int
    is_active: bool
