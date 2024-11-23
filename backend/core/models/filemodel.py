import os
from datetime import datetime
from typing import Any, Optional, Self
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import DATETIME, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from .. import errors
from ..db import Base
from ... import config

UPLOAD_DIRECTORY = "static"


class UploadFileModel(Base):
    __tablename__ = 'upload_files'
    __table_args__ = (
        Index('idx_file_name', 'name', 'extension'),
        Index('idx_file_path', 'path', unique=True)
    )

    pk: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    extension: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[str] = mapped_column(String(250), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.pk', ondelete='CASCADE'), nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created: Mapped[datetime] = mapped_column(DATETIME, default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DATETIME, default=func.now(), onupdate=func.now, nullable=False)

    owner = relationship('ModelUser', back_populates='uploaded_files')

    async def upload(self: Self, session: Session, file: UploadFile, *, sub_directories: str = 'uploads') -> Any | str:
        path = await upload_file(file, sub_directories=sub_directories)

        try:
            self.path = path.replace('\\', '/')
            print(self.path)
            session.add(self)
            session.commit()
            session.refresh(self)
            return path
        except Exception as error:
            await delete_file(path)
            session.rollback()
            raise ValueError(f"Error uploading the file: {str(error)}")

    async def delete(self: Self, session: Session) -> bool:
        if not self.path:
            raise errors.FILE_NOT_FOUND_ERROR

        try:
            was_deleted = await delete_file(self.path)

            if was_deleted:
                session.delete(self)
                session.commit()

            return was_deleted
        except Exception as error:
            session.rollback()
            raise ValueError(f"Error deleting the file: {str(error)}")

    @property
    def full_name(self: Self) -> str:
        return f'{self.name}{self.extension}'

    @property
    def is_uploaded(self: Self) -> bool:
        return bool(self.path)

    @property
    def absolute_path(self: Self) -> Optional[str]:
        return get_file_path(self.path)

    def __str__(self: Self) -> str:
        return f"UploadFileModel(pk={self.pk}, name={self.name}, extension={self.extension}, path={self.path}, owner_id={self.owner_id}, content_type={self.content_type}, created={self.created}, updated={self.updated})"


async def upload_file(
    file: UploadFile,
    *,
    sub_directories: str = 'uploads'
) -> Any | str:
    dir_path: str = __make_dirs(os.path.join(UPLOAD_DIRECTORY, sub_directories))
    file_name: str = __get_hashes_file_name(file.filename)  # type: ignore
    file_path: str = os.path.join(dir_path, file_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return file_path


async def delete_file(
    file_url: str
) -> bool:
    file_path = os.path.join(config.BASE_DIR, file_url)

    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def get_file_path(
    file_url: str,
) -> str | None:
    file_path = os.path.join(config.BASE_DIR, file_url)
    return file_path if os.path.exists(file_path) else None


def __get_hashes_file_name(filename: str) -> str:
    unique_id = uuid4().hex[:16]
    return f'file_{unique_id}_{filename}'


def __make_dirs(dir_path: str) -> str:
    os.makedirs(dir_path, exist_ok=True)
    return dir_path
