from typing import Annotated

from pydantic import (BaseModel, Field, EmailStr)

from .task import TaskSchema


class UserBase(BaseModel):
    email: EmailStr
    first_name: Annotated[str, Field(max_length=255)]
    last_name: Annotated[str, Field(max_length=255)]


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, examples=['12345678'])]
    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'first_name': 'Carl',
                    'last_name' : 'Johnson',
                    'example': 'example@example.com',
                    'password': '********'
                }
            ]
        }
    }


class UserEdit(UserBase):
    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'first_name': 'Carl',
                    'last_name' : 'Johnson',
                    'example': 'example@example.com'
                }
            ]
        }
    }


class UserSchema(UserBase):
    pk: int
    is_active: bool
    tasks: list['TaskSchema']

    model_config = {
        'from_attributes': True
    }


class UserDetails(UserSchema):
    model_config = {
        'from_attributes': True
    }
