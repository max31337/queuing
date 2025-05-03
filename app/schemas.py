from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from enum import Enum

class QueueStatus(str, Enum):
    waiting = "waiting"
    processing = "processing"
    done = "done"
    skipped = "skipped"
    
class QueueCreate(BaseModel):
    type: str  # Transaction type (e.g., Inquiry, Deposit, Withdrawal)
    status: Optional[QueueStatus] = QueueStatus.waiting  # Default status is 'waiting'
    timestamp: Optional[datetime] = None  # Optional timestamp, defaults to current time

class QueueUpdate(BaseModel):
    status: QueueStatus  # Update only the status

class QueueRead(BaseModel):
    id: int
    queue_number: str  # Include formatted queue number
    type: str
    status: str
    timestamp: datetime
    date: date  # Include the date field

    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode for SQLAlchemy compatibility
