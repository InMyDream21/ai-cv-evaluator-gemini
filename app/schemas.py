from pydantic import BaseModel
from typing import Optional, Dict, Any

class UploadResponse(BaseModel):
    upload_id: int

class EvaluateResponse(BaseModel):
    id: int
    status: str

class JobResult(BaseModel):
    id: int
    status: str
    result: Optional[Dict[str, Any]] = None

    class Config:
        extra = "ignore"
        exclude_none = True
        exclude_null = True