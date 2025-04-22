from pydantic import BaseModel
from datetime import datetime

class QueueCreate(BaseModel):
    type: str
    status: str
    timestamp: datetime | None = None

class QueueRead(BaseModel):
    id: int
    type: str
    status: str
    timestamp: datetime

    class Config:
        orm_mode = True
