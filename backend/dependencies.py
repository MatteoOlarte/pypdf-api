from typing import Any, Annotated, Generator

import jwt
from fastapi import UploadFile, File, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.core.models.user import ModelUser

from . import config
from .core.db import SessionLocal
from .core.utils import file_utils
from .core.utils import user_utils
from .core import errors

oauth2 = OAuth2PasswordBearer(tokenUrl='/accounts/authenticate/sign-in')


def get_db() -> Generator[Session, Any, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def file_uploads(files: Annotated[list[UploadFile], File(...)]) -> list[UploadFile]:
    file_utils.check_size_or_raise(files, config.MAX_FILE_SIZE)
    return files


def file_upload(file: Annotated[UploadFile, File(...)]) -> UploadFile:
    file_utils.check_size_or_raise([file], config.MAX_FILE_SIZE)
    return file


def get_current_user(
        db: Annotated[Session, Depends(get_db)],
        token: Annotated[str, Depends(oauth2)]
) -> ModelUser:
    """
    Retrieve the current authenticated user from the database.

    This dependency ensures that the user making the request is authenticated
    and has a valid session. It is similar to a "login required" check. 
    The function decodes the provided JWT token to extract the user's email
    and fetches the user from the database. If the token is invalid, the user
    is not found, or the user's account is inactive, an appropriate HTTPException
    is raised.

    Args:
        db (Session): Database session dependency.
        token (str): JWT token used for authenticating the user.

    Returns:
        ModelUser: The authenticated and active user object.

    Raises:
        HTTPException: If the token is invalid, the user does not exist, or the
                       user's account is inactive.
    """
    user_db = ...
    email = ...

    try:
        payload = jwt.decode(token, config.SECRET_KEY, [config.ALGORITHM]) # type: ignore
        email = payload.get('sub')
    except jwt.PyJWTError:
        raise errors.INVALID_CREDENTIALS_ERROR
    
    user_db = user_utils.get_by_email(db, email=email)

    if not user_db:
        raise errors.USER_NOT_FOUND_ERROR
    if not user_db.is_active: 
        raise errors.INACTIVE_USER_ERROR
    return user_db
