from fastapi import FastAPI

from .routers import (pdf_files)

app = FastAPI()
app.include_router(pdf_files.router)
