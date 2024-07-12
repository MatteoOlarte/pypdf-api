import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core.models.user import ModelUser
from ..core.schemas import user as user_schemas
from ..core.schemas.token import Token
from ..core.utils import user_utils
from ..dependencies import get_db, get_current_user

load_dotenv('.env')
router = APIRouter(
    prefix='/auth',
    tags=['Accounts']
)
SECRET_KEY = os.getenv('T_KEY')
ALGORITHM = os.getenv('E_ALGORITHM')
oauth2 = OAuth2PasswordBearer(tokenUrl='/auth/signin')


def __authenticate_user(db: Session, *, user_email: str, password: str) -> None | ModelUser:
    db_user: ModelUser = user_utils.get_by_email(db, email=user_email)

    if not db_user:
        return None
    if not user_utils.validate_password(password, db_user.password):  # type: ignore
        return None
    return db_user


def __create_token(data: dict[str, Any], *, expires_delta: timedelta = timedelta(minutes=5)):
    json_token = data.copy()
    expire_date = datetime.now(timezone.utc) + expires_delta
    json_token.update({'exp': expire_date})
    return jwt.encode(json_token, SECRET_KEY, ALGORITHM)


@router.post('/signup', response_model=user_schemas.PublicUser, status_code=status.HTTP_201_CREATED)
async def create_user(
        user_in: user_schemas.AuthUser,
        db: Annotated[Session, Depends(get_db)]
) -> ModelUser:
    user_db: ModelUser = user_utils.get_by_email(db, email=user_in.email)
    create = ...

    if user_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='email already registered',
            headers={
                'X-Error': 'EmailAlreadyRegistered'
            }
        )
    create = user_utils.create_user(db, user_in=user_in)
    return create


@router.post('/signin', response_model=Token)
async def user_signin(
        auth_form: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[Session, Depends(get_db)]
):
    user = __authenticate_user(db, user_email=auth_form.username, password=auth_form.password)
    token = ...

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Could not validate user, invalid credentials',
            headers={
                'X-Error': 'InvalidCredentials'
            }
        )
    token = __create_token({'sub': user.email}, expires_delta=timedelta(minutes=1))
    return {'access_token': token, 'token_type': 'bearer'}


@router.get('/my-profile', response_model=user_schemas.PublicUser)
async def user_profile(current: Annotated[ModelUser, Depends(get_current_user)]):
    return current
