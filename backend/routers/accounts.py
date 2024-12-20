import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import config
from ..core import errors
from ..core.models.user import User
from ..core.schemas import Token
from ..core.schemas import user as schemas
from ..core.utils import user_utils
from ..dependencies import current_user_or_raise, get_db

router = APIRouter(
    prefix='/accounts',
    tags=['Accounts']
)
SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.ALGORITHM


def __authenticate_user(db: Session, *, user_email: str, password: str) -> User:
    db_user: User = user_utils.get_by_email(db, email=user_email)

    if not db_user:
        raise errors.USER_NOT_FOUND_ERROR
    if not db_user.validate_password(password):  
        raise errors.INVALID_CREDENTIALS_ERROR
    if not db_user.is_active:
        raise errors.INACTIVE_USER_ERROR
    return db_user


def __create_token(data: dict[str, Any], *, expires_delta: timedelta = timedelta(minutes=5)) -> str:
    json_token = data.copy()
    expire_date = datetime.now(timezone.utc) + expires_delta
    json_token.update({'exp': expire_date})
    return jwt.encode(json_token, SECRET_KEY, ALGORITHM) # type: ignore


@router.post('/authenticate/sign-up', response_model=schemas.UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
        user_in: schemas.UserCreate,
        db: Annotated[Session, Depends(get_db)]
) -> User:
    user_db: User = user_utils.get_by_email(db, email=user_in.email)
    create = ...

    if user_db:
        raise errors.EMAIL_IN_USE_ERROR
    create = user_utils.create_user(db, user_in=user_in)
    return create


@router.post('/authenticate/sign-in', response_model=Token)
def login_user(
    auth_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
) -> dict[str, str]:
    user = __authenticate_user(db, user_email=auth_form.username, password=auth_form.password)
    token = __create_token({'sub': user.email}, expires_delta=timedelta(minutes=30))

    return {'access_token': token, 'token_type': 'bearer'}


@router.put('/authenticate/edit', response_model=schemas.UserSchema)
async def edit_user(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user_or_raise)],
    edit: schemas.UserEdit
) -> User:
    user.first_name = edit.first_name
    user.last_name = edit.last_name
    user.email = edit.email
    user.update(db)
    return user


@router.get('/users/current', response_model=schemas.UserSchema)
def user_profile(user: Annotated[User, Depends(current_user_or_raise)]) -> User:
    return user
