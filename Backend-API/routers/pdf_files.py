import io
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
    print('writing')
    pdf_writer.write(buffer)
    print('done')
    buffer.seek(0)
    print('returning')
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


def _upload_files(files: Annotated[list[UploadFile], File(...)]) -> list[UploadFile]:
    _validate_size_or_raise(files)
    return files


@router.post('/merge')
async def merge_pdf(
        upload_files: Annotated[list[UploadFile], Depends(_upload_files)],
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
