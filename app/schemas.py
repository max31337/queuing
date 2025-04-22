from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class QueueCreate(BaseModel):
    type: str
    status: Optional[str] = "pending"  # or Required
    timestamp: datetime | None = None

class QueueRead(BaseModel):
    id: int
    type: str
    status: str
    timestamp: datetime

    class Config:
        orm_mode = True
