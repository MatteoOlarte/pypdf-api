import io
import zipfile
from typing import Annotated

import pypdf
from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    status,
    Depends,
    File,
    Query
)
from fastapi.responses import StreamingResponse
from pypdf.errors import PyPdfError

MAX_FILE_SIZE = 200
router = APIRouter(prefix='/pdf_files', tags=['PDF Utilities'])
non_pdf_error = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='file is not a PDF',
    headers={
        'X-Error': 'NonPDFFile'
    }
)


def _to_bytes(pdf_writer: pypdf.PdfWriter) -> io.BytesIO:
    buffer = io.BytesIO()
    pdf_writer.write(buffer)
    buffer.seek(0)
    return buffer


def _validate_size_or_raise(upload_files: Annotated[list[UploadFile], File(...)]) -> None:
    file_size = sum(file.size for file in upload_files) / 1_000_000
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'file size is larger than {MAX_FILE_SIZE:<1}mb limit',
            headers={
                'X-Error': 'FileTooLarge'
            }
        )


def file_uploads(files: Annotated[list[UploadFile], File(...)]) -> list[UploadFile]:
    _validate_size_or_raise(files)
    return files


def file_upload(file: Annotated[UploadFile, File(...)]) -> UploadFile:
    _validate_size_or_raise([file])
    return file


def zip_files(files: dict[str, pypdf.PdfWriter]):
    zip_io = io.BytesIO()

    with zipfile.ZipFile(zip_io, 'w') as zip_file:
        for name, i in files.items():
            file_io = _to_bytes(i)
            zip_file.writestr(f'{name}', file_io.getvalue())

    return zip_io


@router.post('/merge')
async def merge_pdf(
        upload_files: Annotated[list[UploadFile], Depends(file_uploads)],
        strict: Annotated[bool, Query(..., description='strict mode')] = False
) -> StreamingResponse:
    """
    Merge multiple PDF files into a single PDF file.
    - **strict**: If false then non-PDF files will be ignored. Otherwise, an error will be raised.
    - **upload_files**: Files to be merged.
    """
    if len(upload_files) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='at least 2 files are required for merging',
            headers={
                'X-Error': 'InsufficientFiles'
            }
        )
    writer = pypdf.PdfWriter()
    headers = {}

    for file in upload_files:
        try:
            await file.seek(0)
            reader = pypdf.PdfReader(file.file)
            writer.append(reader)
        except PyPdfError:
            if strict:
                raise non_pdf_error
            continue
    headers.update({
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'attachment; filename=merged_pdf.pdf'
    })
    return StreamingResponse(
        content=iter([_to_bytes(writer).getvalue()]),
        media_type='application/pdf',
        headers=headers
    )


@router.post('/protect')
async def protect_pdf(
        uploaded_files: Annotated[list[UploadFile], Depends(file_uploads)],
        user_password: Annotated[str, Query(..., description='password to protect the PDF file')],
        strict: Annotated[bool, Query(..., description='strict mode')] = False
):
    """
    Protect a PDF file with a password.
    - **uploaded_files**: Files to be protected.
    - **password**: Password to protect the PDF file.
    """
    pdf_files: dict[str, pypdf.PdfWriter] = {}
    zip_file = ...

    for file in uploaded_files:
        await file.seek(0)

        try:
            reader = pypdf.PdfReader(file.file)
            writer = pypdf.PdfWriter()
            writer.append(reader)
            writer.encrypt(user_password, None, True)
            pdf_files.update({f'{file.filename}': writer})
        except PyPdfError:
            if strict:
                raise non_pdf_error
            continue

    zip_file = zip_files(pdf_files)
    headers = {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'attachment; filename=protected_pdf.zip'
    }
    return StreamingResponse(
        content=iter([zip_file.getvalue()]),
        media_type='application/zip',
        headers=headers
    )


@router.post('/unlock')
async def unlock_pdf(
        upload_file: Annotated[UploadFile, Depends(file_upload)],
        password: Annotated[str, Query(..., description='password to unlock the PDF file')]
):
    """
    Unlock a PDF file with a password.
    - **upload_file**: File to be unlocked.
    - **password**: Password to unlock the PDF file.
    """
    file_name = upload_file.filename
    file_io = ...
    headers = ...

    try:
        reader = pypdf.PdfReader(upload_file.file)
        writer = ...

        if reader.is_encrypted:
            reader.decrypt(password)
        writer = pypdf.PdfWriter(clone_from=reader)
        file_io = _to_bytes(writer)
    except PyPdfError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='invalid password',
            headers={
                'X-Error': 'InvalidPDFPassword'
            }
        )
    headers = {
        'Content-Type': 'application/pdf',
        f'Content-Disposition': f'attachment; filename={file_name}'
    }
    return StreamingResponse(
        content=iter([file_io.getvalue()]),
        media_type='application/pdf',
        headers=headers
    )
