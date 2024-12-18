from typing import Annotated

from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..core.models import User, Task
from ..core.schemas import TaskSchema
from ..core.services import tasks_service as ts
from ..core.services import storage_service as ss
from ..dependencies import current_user_or_none, get_db, get_task
from ..core import errors

router = APIRouter(prefix='/tasks', tags=['Tasks'])


async def __delete_result(task_id:int, db: Session):
    task = db.query(Task).where(Task.pk == task_id).first()
    file = task.result # type: ignore

    if file:
        await file.delete(db, ss.LocalExistingFile(file.path))

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


@router.get('/download/{task_id}')
async def download(
        background_tasks: BackgroundTasks,
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[User, Depends(current_user_or_none)],
        task: Annotated[Task, Depends(get_task)],
) -> FileResponse:
    filemodel = task.result

    if not filemodel or not filemodel.absolute_path:
        raise errors.FILE_NOT_FOUND_ERROR
    if task.check_ownership(user):
        background_tasks.add_task(__delete_result, task.pk, db)
        return FileResponse(
            filemodel.absolute_path,
            filename=filemodel.full_name,
            media_type=filemodel.content_type,
            headers={"Content-Disposition": f"attachment; filename={filemodel.full_name}"}
        )

    raise errors.FILE_ACCESS_DENIED
