from typing import Optional
from datetime import datetime

from pydantic import BaseModel


from .filemodel import FileModelSchema

class TaskSchema(BaseModel):
    pk: int
    created: datetime
    updated: datetime
    status: 'StatusSchema'
    process: 'TaskProcess'
    result: Optional['FileModelSchema'] = None

    model_config = {
        'from_attributes': True
    }
    

class StatusSchema(BaseModel):
    pk: int
    name: str

    model_config = {
        'from_attributes': True
    }


class TaskProcess(BaseModel):
    pk: int
    name: str

    model_config = {
        'from_attributes': True
    }