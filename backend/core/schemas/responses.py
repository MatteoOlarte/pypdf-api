from pydantic import BaseModel


class ProcessResponse(BaseModel):
    download_filename: str
    download_path: str
    output_filenumber: int
    timer: float
    task_status: str
    task_name: str
