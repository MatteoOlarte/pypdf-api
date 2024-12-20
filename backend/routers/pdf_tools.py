from typing import Annotated

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..core import errors
from ..core.models import Task, User
from ..core.schemas import TaskSchema
from ..core.services.storage_service import LocalExistingFile
from ..core.services import tasks_service as ts
from ..core.utils import pdf_utils
from ..dependencies import get_db, get_task, current_user_or_none

router = APIRouter(prefix='/pdf-utilities', tags=['PDF Utilities'])


async def __clear_files(db: Session, task_id: int):
    strategy = LocalExistingFile('')
    task = db.query(Task).where(Task.pk == task_id).first()
    files = task.files # type: ignore

    for filemodel in files:
        await filemodel.delete(db, strategy)


@router.post('/merge', response_model=TaskSchema)
async def merge_pdf(
        background_tasks: BackgroundTasks,
        db: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[User, Depends(current_user_or_none)],
        strict: Annotated[bool, Query(..., description='strict mode')] = False
) -> Task:
    """
    Merge multiple PDF files into a single PDF file.
    - **strict**: If false then non-PDF files will be ignored. Otherwise, an error will be raised.
    - **upload_files**: Files to be merged.
    """
    background_tasks.add_task(__clear_files, db, task.pk)
    if not task.check_ownership(user):
        raise errors.FORBIDDEN_TASK
    if ts.is_completed(task):
        raise errors.COMPLETED_TASK

    try:
        task.result = await pdf_utils.merge_pdf(db, task, strict)
        ts.set_task_completed(task)
        ts.set_process(task, ts.ProcessTypes.MERGE)
        task.update(db)
        return task
    except Exception as error:
        ts.set_task_failed(task)
        task.update(db)
        raise error


@router.post('/lock', response_model=TaskSchema)
async def lock_pdf(
        background_tasks: BackgroundTasks,
        db: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[User, Depends(current_user_or_none)],
        password: Annotated[str, Query(..., description='password to unlock the PDF file')]
) -> Task:
    """
    Protect a PDF file with a password.
    - **uploaded_files**: Files to be protected.
    - **password**: Password to protect the PDF file.
    """
    background_tasks.add_task(__clear_files, db, task.pk)
    if not task.check_ownership(user):
        raise errors.FORBIDDEN_TASK
    if ts.is_completed(task):
        raise errors.COMPLETED_TASK

    try:
        task.result = await pdf_utils.lock_pdf(db, task, password)
        ts.set_task_completed(task)
        ts.set_process(task, ts.ProcessTypes.LOCK)
        task.update(db)
        return task
    except Exception as error:
        ts.set_task_failed(task)
        task.update(db)
        raise error


@router.post('/unlock', response_model=TaskSchema)
async def unlock_pdf(
        background_tasks: BackgroundTasks,
        db: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[User, Depends(current_user_or_none)],
        password: Annotated[str, Query(..., description='password to unlock the PDF file')]
) -> Task:
    """
    Unlock a PDF file with a password.
    - **upload_file**: File to be unlocked.
    - **password**: Password to unlock the PDF file.
    """
    background_tasks.add_task(__clear_files, db, task.pk)
    if not task.check_ownership(user):
        raise errors.FORBIDDEN_TASK
    if ts.is_completed(task):
        raise errors.COMPLETED_TASK

    try:
        task.result = await pdf_utils.unlock_pdf(db, task, password)
        ts.set_task_completed(task)
        ts.set_process(task, ts.ProcessTypes.UNLOCK)
        task.update(db)
        return task
    except Exception as error:
        ts.set_task_failed(task)
        task.update(db)
        raise error
    

@router.post('/split/range', response_model=TaskSchema)
async def split_pdf(
        background_tasks: BackgroundTasks,
        db: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[User, Depends(current_user_or_none)],
        ranges: Annotated[list[int], Query()],
        merge_after: bool = False
) -> Task:
    background_tasks.add_task(__clear_files, db, task.pk)
    if not task.check_ownership(user):
        raise errors.FORBIDDEN_TASK
    if ts.is_completed(task):
        raise errors.COMPLETED_TASK
    
    try:
        task.result = await pdf_utils.rangesplit_pdf(db, task, ranges, merge_after)
        ts.set_task_completed(task)
        ts.set_process(task, ts.ProcessTypes.SPLIT)
        task.update(db)
        return task
    except Exception as error:
        ts.set_task_failed(task)
        task.update(db)
        raise error
    

@router.post('/split/pages', response_model=TaskSchema)
async def extract_pages(
        background_tasks: BackgroundTasks,
        db: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[User, Depends(current_user_or_none)],
        pages: Annotated[list[int], Query()],
        merge_after: bool = False
) -> Task:
    background_tasks.add_task(__clear_files, db, task.pk)
    if not task.check_ownership(user):
        raise errors.FORBIDDEN_TASK
    if ts.is_completed(task):
        raise errors.COMPLETED_TASK
    
    try:
        task.result = await pdf_utils.pagesplit_pdf(db, task, pages, merge_after)
        ts.set_task_completed(task)
        ts.set_process(task, ts.ProcessTypes.SPLIT)
        task.update(db)
        return task
    except Exception as error:
        ts.set_task_failed(task)
        task.update(db)
        raise error