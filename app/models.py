from sqlalchemy import Column, Integer, String, Enum, DateTime, Date, Boolean
from datetime import datetime, date
from .database import Base
from .schemas import QueueStatus  # Use the same Enum as in schemas.py

class QueueEntry(Base):
    __tablename__ = "queue"

    id = Column(Integer, primary_key=True, index=True)
    queue_number = Column(String, nullable=False)  # Store formatted queue number (e.g., INQ001)
    type = Column(String, nullable=False)  # Transaction type (e.g., Inquiry, Deposit, Withdrawal)
    status = Column(Enum(QueueStatus), default=QueueStatus.waiting, nullable=False)  # Default status is 'waiting'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)  # Timestamp of the transaction
    date = Column(Date, default=date.today, nullable=False)  # Date of the transaction
    archived = Column(Boolean, default=False, nullable=False)  # New field to track archived entries