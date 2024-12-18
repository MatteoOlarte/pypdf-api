from datetime import datetime
from typing import TYPE_CHECKING, Optional, Self

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from ..db import Base

if TYPE_CHECKING:
    from . import FileModel, User


class Task(Base):
    __tablename__ = "tasks"

    pk: Mapped[int] = mapped_column(Integer, name='task_id', primary_key=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    process_id: Mapped[int] = mapped_column(ForeignKey('task_process_type.process_id', ondelete='RESTRICT'), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey('task_status.status_id', ondelete='RESTRICT'), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    result_id: Mapped[Optional[int]] = mapped_column(ForeignKey('files.file_id', ondelete='SET NULL'), nullable=True, unique=True)
    
    process: Mapped['TaskProcess'] = relationship(back_populates='tasks', foreign_keys='Task.process_id')
    status: Mapped['TaskStatus'] = relationship(back_populates='tasks', foreign_keys='Task.status_id')
    user: Mapped[Optional['User']] = relationship(back_populates='tasks', foreign_keys='Task.user_id')
    result: Mapped[Optional['FileModel']] = relationship(foreign_keys='Task.result_id')
    files: Mapped[list['FileModel']] = relationship(back_populates='task', foreign_keys='FileModel.task_id')

    def update(self: Self, db: Session) -> None:
        self.updated = func.now()
        db.add(self)
        db.commit()
        db.refresh(self)

    def check_ownership(self: Self, user: Optional['User']) -> bool:
        if not self.user:
            return True
        if user and self.user == user:
            return True
        return False

    def add_file(self: Self, filemodel: 'FileModel', db: Session) -> Self:
        if self.files:
            self.files.append(filemodel)
        else:
            self.files = [filemodel]
        self.update(db)
        return self

    def __eq__(self: Self, other) -> bool:
        return self.pk == other.pk

    def __str__(self: Self) -> str:
        return f'Task=(pk={self.pk}, created=\"{self.created}\", updated=\"{self.updated}\", status=\"{self.status}\")'


class TaskStatus(Base):
    __tablename__ = "task_status"

    pk: Mapped[int] = mapped_column(Integer, name='status_id', primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    tasks: Mapped[list['Task']] = relationship(back_populates='status')

    def __eq__(self: Self, other) -> bool:
        return self.pk == other.pk

    def __str__(self: Self) -> str:
        return f'{self.name}'

    def __repr__(self: Self) -> str:
        return f'TaskStatus=(pk={self.pk}, name=\"{self.name}\")'
    

class TaskProcess(Base):
    __tablename__ = 'task_process_type'

    pk: Mapped[int] = mapped_column(Integer, name='process_id', primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    tasks: Mapped[list['Task']] = relationship(back_populates='process')

    def __eq__(self: Self, other) -> bool:
        return self.pk == other.pk

    def __str__(self: Self) -> str:
        return f'{self.name}'
