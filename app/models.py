from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class QueueEntry(Base):
    __tablename__ = "queue"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False, default='waiting')
    timestamp = Column(DateTime, default=datetime.utcnow)
