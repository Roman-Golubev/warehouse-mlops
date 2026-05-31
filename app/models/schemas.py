from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class ResultResponse(BaseModel):
    task_id: str
    status: str
    predictions: Optional[List[float]] = None
    model_color: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
