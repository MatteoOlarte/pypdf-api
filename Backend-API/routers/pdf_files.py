import io
from typing import Annotated

import pypdf
from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    status
)
from starlette.responses import StreamingResponse
from pypdf.errors import PyPdfError

router = APIRouter(prefix='/pdf_files', tags=['PDF Utilities'])


def to_bytes(pdf_writer: pypdf.PdfWriter) -> io.BytesIO:
    buffer = io.BytesIO()
    print('writing')
    pdf_writer.write(buffer)
    print('done')
    buffer.seek(0)
    print('returning')
    return buffer


@router.post('/merge_pdf')
async def merge_pdf(upload_files: Annotated[list[UploadFile], File(...)]) -> StreamingResponse:
    if len(upload_files) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='at least 2 files are required for merging',
            headers={
                'X-Error': 'InsufficientFiles'
            }
        )
    file_size = sum(file.size for file in upload_files) / 1_000_000
    writer = pypdf.PdfWriter()
    headers = {}

    if file_size > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='file size is too large',
            headers={
                'X-Error': 'FileTooLarge'
            }
        )

    for file in upload_files:
        try:
            await file.seek(0)
            reader = pypdf.PdfReader(file.file)
            writer.append(reader)
        except PyPdfError:
            continue
    headers.update({
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'attachment; filename=merged_pdf.pdf'
    })
    return StreamingResponse(
        content=iter([to_bytes(writer).getvalue()]),
        media_type='application/pdf',
        headers=headers
    )
