from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

def create_queue(db: Session, item: schemas.QueueCreate):
    db_item = models.QueueEntry(type=item.type)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_all_queue(db: Session):
    return db.query(models.QueueEntry).order_by(models.QueueEntry.timestamp).all()
