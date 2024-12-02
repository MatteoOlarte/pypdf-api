from typing import Any, Annotated, Generator, Optional

import jwt
from fastapi import UploadFile, File, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import config
from .core.db import SessionLocal
from .core.models import ModelUser
from .core.utils import file_utils
from .core.utils import user_utils
from .core import errors

__oauth2 = OAuth2PasswordBearer(tokenUrl='/accounts/authenticate/sign-in', auto_error=False)


def get_db() -> Generator[Session, Any, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user_or_none(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[Optional[str], Depends(__oauth2)]
) -> Optional[ModelUser]:
    '''
    Retrieve the current authenticated user from the database, returning None 
    if the user is not found, inactive, or if the token is invalid.

    This dependency attempts to authenticate the user based on the provided 
    JWT token. If the token is valid, the function fetches the user from the 
    database. If any error occurs (invalid token, missing user, or inactive 
    account), it returns None.

    Args:
        db (Session): Database session dependency.
        token (str): JWT token used for authenticating the user.

    Returns:
        Optional[ModelUser]: The authenticated and active user object if successful,
                             or None if any error occurs.
    '''
    if not token:
        return None

    try:
        user = __get_current_user(db, token)
        return user
    except HTTPException:
        return None


def current_user_or_raise(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(__oauth2)]
) -> ModelUser:
    '''
    Retrieve the current authenticated user from the database, raising exceptions
    for invalid credentials, inactive accounts, or missing users.

    This dependency ensures that the user making the request is authenticated 
    and authorized. The function decodes the provided JWT token to extract the 
    user's email and fetches the corresponding user from the database. If the 
    token is invalid, the user does not exist, or the account is inactive, an 
    appropriate exception will be raised.

    Args:
        db (Session): Database session dependency.
        token (str): JWT token used for authenticating the user.

    Returns:
        ModelUser: The authenticated and active user object.

    Raises:
        INVALID_CREDENTIALS_ERROR: If the JWT token is invalid or malformed.
        USER_NOT_FOUND_ERROR: If no user is found for the provided email.
        INACTIVE_USER_ERROR: If the user exists but their account is inactive.
    '''
    return __get_current_user(db, token)


def file_uploads(files: Annotated[list[UploadFile], File(...)]) -> list[UploadFile]:
    file_utils.check_size_or_raise(files, config.MAX_FILE_SIZE)
    return files


def file_upload(
    file: Annotated[UploadFile, File(...)]
) -> UploadFile:
    file_utils.check_size_or_raise([file], config.MAX_FILE_SIZE)
    return file


def __get_current_user(
    db: Session,
    token: Optional[str]
) -> ModelUser:
    user_db = ...
    email = ...

    try:
        payload = jwt.decode(token, config.SECRET_KEY, [config.ALGORITHM])  # type: ignore
        email = payload.get('sub')
    except jwt.PyJWTError:
        raise errors.INVALID_CREDENTIALS_ERROR

    user_db = user_utils.get_by_email(db, email=email)

    if not user_db:
        raise errors.USER_NOT_FOUND_ERROR
    if not user_db.is_active:
        raise errors.INACTIVE_USER_ERROR
    return user_db
