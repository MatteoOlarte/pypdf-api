from datetime import datetime

from pydantic import BaseModel


class FileModelSchema(BaseModel):
    pk: int
    full_name: str
    content_type: str
    path: str
    created: datetime
    updated: datetime
    is_uploaded: bool

    model_config = {
        'from_attributes': True
    }