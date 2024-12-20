from enum import Enum
from typing import Sequence, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Task, TaskStatus, TaskProcess, User


class StatusesTypes(Enum):
    CREATED = TaskStatus(pk=1, name='task_created')
    IN_PROGRES = TaskStatus(pk=2, name='task_in_progress')
    COMPLETED = TaskStatus(pk=3, name='task_completed')
    FAILED = TaskStatus(pk=4, name='task_failed')
    CANCELED = TaskStatus(pk=5, name='task_canceled')
    DOWLOADED = TaskStatus(pk=6, name='task_dowloaded')


class ProcessTypes(Enum):
    UNDEFINED = TaskProcess(pk=1, name='undefined')
    MERGE = TaskProcess(pk=2, name='pdf_merge')
    LOCK = TaskProcess(pk=3, name='pdf_lock')
    UNLOCK = TaskProcess(pk=4, name='pdf_unlock')
    SPLIT = TaskProcess(pk=5, name='pdf_split')


def create_task(db: Session, /, *, user: Optional[User]) -> Task:
    task: Task = Task()
    task.status_id = StatusesTypes.CREATED.value.pk
    task.result = None
    task.user = user
    task.process_id = ProcessTypes.UNDEFINED.value.pk
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, /, *, task_id: int) -> Task:
    task: Task = db.query(Task).where(Task.pk == task_id).first()
    return task


def set_task_in_progress(task: Task) -> Task:
    task.status_id = StatusesTypes.IN_PROGRES.value.pk
    return task


def set_task_completed(task: Task) -> Task:
    task.status_id = StatusesTypes.COMPLETED.value.pk
    return task


def set_task_failed(task: Task) -> Task:
    task.status_id = StatusesTypes.FAILED.value.pk
    return task


def set_task_canceled(task: Task) -> Task:
    task.status_id = StatusesTypes.CANCELED.value.pk
    return task


def download_ready(task: Task) -> bool:
    return task.status == StatusesTypes.COMPLETED.value


def is_completed(task: Task) -> bool:
    return task.status == StatusesTypes.COMPLETED.value or task.status == StatusesTypes.DOWLOADED.value


def set_task_dowloaded(task: Task) -> Task:
    task.status_id = StatusesTypes.DOWLOADED.value.pk
    return task


def set_process(task: Task, process: ProcessTypes) -> Task:
    task.process_id = process.value.pk
    return task


def init_service(db: Session) -> None:
    s_results: Sequence[int] = db.execute(select(TaskStatus.pk)).scalars().all()
    p_results: Sequence[int] = db.execute(select(TaskProcess.pk)).scalars().all()

    try:
        statuses: list[TaskStatus] = [
            TaskStatus(pk=s.value.pk, name=s.value.name) for s in StatusesTypes if s.value.pk not in s_results
        ]
        processes: list[TaskProcess] = [
            TaskProcess(pk=p.value.pk, name=p.value.name) for p in ProcessTypes if p.value.pk not in p_results
        ]

        if len(statuses) > 0:
            db.add_all(statuses)
            db.commit()
        if len(processes) > 0:
            db.add_all(processes)
            db.commit()
    except Exception as error:
        print(error)
        db.rollback()
