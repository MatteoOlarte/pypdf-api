from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status, UploadFile
from sqlalchemy.orm import Session

from ..core import errors
from ..core.models import User, Task, FileModel
from ..core.schemas import FileModelSchema
from ..core.services import storage_service as ss
from ..core.services import tasks_service as ts
from ..core.utils import file_utils
from ..dependencies import current_user_or_none, get_db, file_upload, get_task, get_file_or_raise

router = APIRouter(prefix='/files', tags=['File Storage'])


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=FileModelSchema)
async def upload_file(
        file: Annotated[UploadFile, Depends(file_upload)],
        session: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[Optional[User], Depends(current_user_or_none)]
) -> FileModel:
    if task.check_ownership(user) and not ts.is_completed(task):
        path = __get_target_path(user)
        file_model = file_utils.UploadFileModelFactory(file, task).create_filemodel()
        strategy = ss.LocalUploadFile(file)
        await file_model.upload(session, strategy, upload_to=path)
        task.update(session)
        return file_model
    raise errors.INVALID_TASK


@router.get('/', response_model=FileModelSchema)
async def get_file(
        filemodel: Annotated[FileModel, Depends(get_file_or_raise)]
) -> FileModel:
    return filemodel


@router.delete('/')
async def delete_file(
        file_url: str,
        session: Annotated[Session, Depends(get_db)],
        user: Annotated[User, Depends(current_user_or_none)]
) -> dict[str, bool]:
    filemodel = file_utils.get_filemodel(session, file_url=file_url)
    strategy = ss.LocalExistingFile(filemodel.path)  # type: ignore

    if not filemodel:
        raise errors.FILE_NOT_FOUND_ERROR
    if (filemodel.task) and (filemodel.task.check_ownership(user)):
        deleted = await filemodel.delete(session, strategy)
        return {'status': deleted}

    raise errors.FILE_ACCESS_DENIED


def __get_target_path(user: Optional[User]) -> str:
    if user:
        return f'{user.email}/uploads'
    return 'temp/uploads'
