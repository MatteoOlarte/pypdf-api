import os
from typing import Any, Annotated, Generator

import jwt
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException, status, File, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .core.db import SessionLocal
from .core.utils import file_utils
from .core.utils import user_utils

load_dotenv('.env')
oauth2 = OAuth2PasswordBearer(tokenUrl='/auth/signin')
SECRET_KEY: str = os.getenv('T_KEY')  # type: ignore
ALGORITHM: str = os.getenv('E_ALGORITHM')  # type: ignore


def get_db() -> Generator[Session, Any, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def file_uploads(files: Annotated[list[UploadFile], File(...)]) -> list[UploadFile]:
    file_utils.check_size_or_raise(files)
    return files


def file_upload(file: Annotated[UploadFile, File(...)]) -> UploadFile:
    file_utils.check_size_or_raise([file])
    return file


def get_current_user(
        db: Annotated[Session, Depends(get_db)],
        token: Annotated[str, Depends(oauth2)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    user_db = ...
    email = ...

    try:
        payload = jwt.decode(token, SECRET_KEY, [ALGORITHM])
        email = payload.get('sub')

    except jwt.PyJWTError:
        raise credentials_exception
    user_db = user_utils.get_by_email(db, email=email)

    if not user_db:
        raise credentials_exception
    if not user_db.is_active:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='The user does not exist. Try again.',
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user_db
