from sqlalchemy import Column, Integer, String, Enum, DateTime
from .schemas import QueueStatus 
from datetime import datetime
from .database import Base

class QueueEntry(Base):
    __tablename__ = "queue"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    status = Column(Enum(QueueStatus), default=QueueStatus.waiting, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
