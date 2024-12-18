from typing import Any, Annotated, Generator, Optional

import jwt
from fastapi import Body, UploadFile, File, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import config
from .core.db import SessionLocal
from .core.models import User, FileModel, Task
from .core.utils import file_utils, user_utils
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
) -> Optional[User]:
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
) -> User:
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


def file_upload(
        file: Annotated[UploadFile, File(...)]
) -> UploadFile:
    '''
    Handles the file upload and checks if the uploaded file exceeds the maximum allowed size.

    This function receives a file, checks whether its size is within the allowed limit specified
    by the application configuration, and returns the uploaded file if the size is valid. If the 
    file exceeds the maximum allowed size, it raises an exception.

    Args:
        file (UploadFile): The file to be uploaded. This should be a valid file object 
                            that is passed to the function.

    Returns:
        UploadFile: The uploaded file if its size is within the allowed limit.

    Raises:
        HTTPException: If the file size exceeds the maximum allowed size, an exception 
                       will be raised with an appropriate error message.
    '''
    file_utils.check_size_or_raise([file], config.MAX_FILE_SIZE)
    return file


def get_task(db: Annotated[Session, Depends(get_db)], task_id: int) -> Task:
    task = db.query(Task).where(Task.pk == task_id).first()

    if task:
        return task
    raise errors.INVALID_TASK


def get_file_or_raise(
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[User, Depends(current_user_or_none)],
        path: Annotated[str, Query(...)]
) -> FileModel:
    '''
    Retrieve a single file model from the database based on the provided path and ensure the user has access to it.

    This function checks if the file exists and whether the current user has the appropriate permissions to access it.
    If the file is not found or if the user is not authorized to access it, an error is raised.

    Args:
        db (Session): The database session used to query the file.
        user (ModelUser): The current user attempting to access the file.
        path (str): The file path to be used for retrieving the file model.

    Returns:
        UploadFileModel: The file model corresponding to the given path.

    Raises:
        errors.FILE_NOT_FOUND_ERROR: If the file is not found in the database.
        errors.FILE_ACCESS_DENIED: If the user does not have access to the file (either because they are not the owner or access is restricted).
    '''
    filemodel = file_utils.get_filemodel(db, file_url=path)

    if not filemodel:
        raise errors.FILE_NOT_FOUND_ERROR
    if (filemodel.task) and (filemodel.task.check_ownership(user)):
        return filemodel

    raise errors.FILE_ACCESS_DENIED


def __get_current_user(
        db: Session,
        token: Optional[str]
) -> User:
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
