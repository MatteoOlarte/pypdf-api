from enum import Enum
from typing import Sequence, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Task, TaskStatus, User, FileModel


class Statuses(Enum):
    CREATED = TaskStatus(pk=1, name='task_created')
    IN_PROGRES = TaskStatus(pk=2, name='task_in_progress')
    COMPLETED = TaskStatus(pk=3, name='task_completed')
    FAILED = TaskStatus(pk=4, name='task_failed')
    CANCELED = TaskStatus(pk=5, name='task_canceled')


def create_task(db: Session, /, *, user: Optional[User]) -> Task:
    task: Task = Task()
    task.status_id = Statuses.CREATED.value.pk
    task.result = None
    task.user = user
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, /, *, task_id: int) -> Task:
    task: Task = db.query(Task).where(Task.pk == task_id).first()
    return task


def set_task_in_progress(db: Session, task: Task) -> Task:
    task.status_id = Statuses.IN_PROGRES.value.pk
    task.update(db)
    return task


def set_task_completed(db: Session, task: Task) -> Task:
    task.status_id = Statuses.COMPLETED.value.pk
    task.update(db)
    return task


def set_task_failed(db: Session, task: Task) -> Task:
    task.status_id = Statuses.FAILED.value.pk
    task.update(db)
    return task


def set_task_canceled(db: Session, task: Task) -> Task:
    task.status_id = Statuses.CANCELED.value.pk
    task.update(db)
    return task


def init_service(db: Session) -> None:
    results: Sequence[int] = db.execute(select(TaskStatus.pk)).scalars().all()

    try:
        statuses: list[TaskStatus] = [
            TaskStatus(pk=s.value.pk, name=s.value.name) for s in Statuses if s.value.pk not in results
        ]
        if len(statuses) > 0:
            db.add_all(statuses)
            db.commit()
    except Exception as error:
        print(error)
        db.rollback()
