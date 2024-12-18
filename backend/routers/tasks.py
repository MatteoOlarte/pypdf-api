from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..core.models import User, Task, FileModel
from ..core.schemas import TaskSchema, FileModelSchema
from ..core.services import tasks_service as ts
from ..dependencies import current_user_or_none, get_db, get_task
from ..core import errors

router = APIRouter(prefix='/tasks', tags=['Tasks'])


@router.post('/start', response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def start_task(
        user: Annotated[User, Depends(current_user_or_none)],
        db: Annotated[Session, Depends(get_db)]
) -> Task:
    task = ts.create_task(db, user=user)
    return task


@router.get('/{task_id}', response_model=TaskSchema)
def get_task_details(
        user: Annotated[User, Depends(current_user_or_none)],
        task: Annotated[Task, Depends(get_task)]
) -> Task:
    if task.check_ownership(user):
        return task
    raise errors.INVALID_TASK


@router.put('/cancel/{task_id}', response_model=TaskSchema)
def cancel_task(
        user: Annotated[User, Depends(current_user_or_none)],
        task: Annotated[Task, Depends(get_task)],
        db: Annotated[Session, Depends(get_db)]
) -> Task:
    if task.check_ownership(user):
        ts.set_task_canceled(db, task=task)
        return task
    raise errors.INVALID_TASK
