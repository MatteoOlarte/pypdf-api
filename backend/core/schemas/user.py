from typing import Annotated

from pydantic import (BaseModel, Field, EmailStr)


class UserBase(BaseModel):
    email: EmailStr
    first_name: Annotated[str, Field(max_length=255)]
    last_name: Annotated[str, Field(max_length=255)]


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, examples=['12345678'])]


class UserSchema(UserBase):
    pk: int
    is_active: bool

    model_config = {
        'from_attributes': True
    }


class UserDetails(UserSchema):
    model_config = {
        'from_attributes': True
    }