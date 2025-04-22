from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class QueueStatus(str, Enum):
    waiting = "waiting"
    processing = "processing"
    done = "done"

class QueueCreate(BaseModel):
    type: str
    status: Optional[str] = "waiting"  
    timestamp: datetime | None = None

class QueueUpdate(BaseModel):
    status: QueueStatus

class QueueRead(BaseModel):
    id: int
    type: str
    status: str
    timestamp: datetime

    class Config:
        orm_mode = True
