from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

def create_queue(db: Session, item: schemas.QueueCreate):
    db_item = models.QueueEntry(type=item.type)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_queue_status(db: Session, queue_id: int, new_status: models.QueueStatus):
    queue_item = db.query(models.Queue).filter(models.Queue.id == queue_id).first()
    if not queue_item:
        return None
    queue_item.status = new_status
    db.commit()
    db.refresh(queue_item)
    return queue_item

def get_all_queue(db: Session):
    return db.query(models.QueueEntry).order_by(models.QueueEntry.timestamp).all()
