from pydantic import BaseModel
from datetime import datetime

class QueueCreate(BaseModel):
    type: str

class QueueRead(QueueCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True  # pydantic v2
