from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from . import routers
from .core import db
from .config import ALLOWED_HOSTS, BASE_DIR

db.Base.metadata.create_all(bind=db.engine)
app = FastAPI(title='iHate PyPDF')
app.include_router(routers.pdf_files.router)
app.include_router(routers.storage.router)
app.include_router(routers.accounts.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['x-error']
)
app.mount('/' + BASE_DIR + '/static', StaticFiles(directory='static'), name='static')
