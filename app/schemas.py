from pydantic import BaseModel
from datetime import datetime

class QueueCreate(BaseModel):
    type: str
    status: str = "waiting"  # optional if not used in model or DB
    timestamp: datetime | None = None

class QueueRead(BaseModel):
    id: int
    type: str
    timestamp: datetime

    class Config:
        orm_mode = True
