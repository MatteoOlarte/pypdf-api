import os
from datetime import datetime
from typing import Optional, Self, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from .. import errors
from ..db import Base
from ..services.storage_service import StorageStrategy
from ... import config

if TYPE_CHECKING:
    from . import Task


class FileModel(Base):
    __tablename__ = 'files'
    __table_args__ = (
        Index('idx_files_name', 'name', 'extension'),
        Index('idx_files_path', 'path', unique=True)
    )

    pk: Mapped[int] = mapped_column(Integer, name='file_id', primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    extension: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.task_id', ondelete='RESTRICT'))

    task: Mapped['Task'] = relationship(back_populates='files', foreign_keys='FileModel.task_id')

    @property
    def full_name(self: Self) -> str:
        return f'{self.name}{self.extension}'

    @property
    def is_uploaded(self: Self) -> bool:
        return bool(self.path)

    @property
    def absolute_path(self: Self) -> str:
        if absolute_path := _get_file_path(self.path):
            return absolute_path
        raise errors.FILE_NOT_FOUND_ERROR

    async def upload(self: Self, db: Session, strategy: StorageStrategy, *, upload_to: str) -> str:
        path = await strategy.upload(upload_to)

        try:
            self.path = path
            db.add(self)
            db.commit()
            db.refresh(self)
            return path
        except Exception as error:
            await strategy.delete(path)
            db.rollback()
            raise ValueError(f"Error uploading the file: {str(error)}")

    async def delete(self: Self, db: Session, strategy: StorageStrategy) -> bool:
        if not self.path:
            raise errors.FILE_NOT_FOUND_ERROR

        try:
            deleted = await strategy.delete(self.path)

            if deleted:
                db.delete(self)
                db.commit()
            return deleted
        except Exception:
            db.rollback()
            return False

    def update(self: Self, db: Session) -> None:
        self.updated = func.now()
        db.add(self)
        db.commit()
        db.refresh(self)

    def __eq__(self: Self, other) -> bool:
        return self.pk == other.pk


def _get_file_path(file_path: str) -> Optional[str]:
    full_path = os.path.join(config.BASE_DIR, file_path)
    return full_path if os.path.exists(file_path) else None
