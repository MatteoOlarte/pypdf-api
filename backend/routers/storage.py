from typing import Annotated

from fastapi import APIRouter, Depends, File, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..core import errors
from ..core.models import UploadFileModel
from ..core.schemas import filemodel
from ..core.utils import file_utils
from ..dependencies import get_db

router = APIRouter(prefix='/file-storage', tags=['File Storage'])


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=filemodel.FileModelSchema)
async def upload_file(
    file: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_db)]
) -> UploadFileModel:
    file_model = file_utils.SimpleUploadFileFactory().create_filemodel(file, None)
    await file_model.upload(session, file)

    return file_model


@router.get('/', response_model=filemodel.FileModelSchema)
async def get_file(
    file_url: str,
    session: Annotated[Session, Depends(get_db)]
) -> UploadFileModel:
    filemodel = file_utils.get_filemodel(session, file_url=file_url)

    if not filemodel:
        raise errors.FILE_NOT_FOUND_ERROR

    return filemodel


@router.delete('/')
async def delete_file(
    file_url: str,
    session: Annotated[Session, Depends(get_db)]
) -> dict[str, bool]:
    filemodel = file_utils.get_filemodel(session, file_url=file_url)

    if not filemodel:
        raise errors.FILE_NOT_FOUND_ERROR

    await filemodel.delete(session)
    return {'status': True}


@router.get('/download')
async def download_file(
    file_url: str,
    session: Annotated[Session, Depends(get_db)]
) -> FileResponse:
    filemodel = file_utils.get_filemodel(session, file_url=file_url)

    if not filemodel or not filemodel.absolute_path:
        raise errors.FILE_NOT_FOUND_ERROR

    return FileResponse(
        filemodel.absolute_path,
        filename=filemodel.full_name,
        media_type=filemodel.content_type,
        headers={"Content-Disposition": f"attachment; filename={filemodel.full_name}"}
    )
