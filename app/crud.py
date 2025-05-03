from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from . import models, schemas
from datetime import datetime, date

def create_queue(db: Session, item: schemas.QueueCreate):
    # Get today's date
    today = date.today()

    # Check the last queue entry for the same type and date
    last_queue = (
        db.query(models.QueueEntry)
        .filter(models.QueueEntry.type == item.type, models.QueueEntry.date == today)
        .order_by(models.QueueEntry.id.desc())
        .first()
    )

    # Reset the queue number if it's a new day
    next_number = (int(last_queue.queue_number[3:]) + 1) if last_queue else 1

    # Generate the formatted queue number
    prefix = {
        "Inquiry": "INQ",
        "Deposit": "DEP",
        "Withdrawal": "WIT"
    }.get(item.type, "UNK")  # Default to "UNK" if type is unknown
    formatted_queue_number = f"{prefix}{next_number:03d}"

    db_item = models.QueueEntry(
        type=item.type,
        queue_number=formatted_queue_number,
        status=item.status or schemas.QueueStatus.waiting,
        timestamp=item.timestamp or datetime.utcnow(),
        date=today  # Save today's date
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_queue_status(db: Session, queue_id: int, new_status: schemas.QueueStatus):
    queue_item = db.query(models.QueueEntry).filter(models.QueueEntry.id == queue_id).first()
    if not queue_item:
        return None

    queue_item.status = new_status

    # If the status is "waiting", update the timestamp to move it to the end of the line
    if new_status == schemas.QueueStatus.waiting:
        queue_item.timestamp = datetime.utcnow()  # Update the timestamp to now

    # If the status is "done", set a timestamp for archiving
    if new_status == schemas.QueueStatus.done:
        queue_item.timestamp = datetime.utcnow()  # Update the timestamp to now

    db.commit()
    db.refresh(queue_item)
    return queue_item

def get_active_queue(db: Session):
    today = datetime.utcnow().date()
    return (
        db.query(models.QueueEntry)
        .filter(
            models.QueueEntry.date == today,
            models.QueueEntry.archived == False  # Only show non-archived entries
        )
        .order_by(models.QueueEntry.timestamp)  # Sort by timestamp
        .all()
    )

def archive_done_entries(db: Session):
    two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
    done_entries = (
        db.query(models.QueueEntry)
        .filter(
            models.QueueEntry.status == schemas.QueueStatus.done,
            models.QueueEntry.timestamp <= two_minutes_ago,
            models.QueueEntry.archived == False
        )
        .all()
    )
    for entry in done_entries:
        entry.archived = True  # Mark as archived
    db.commit()
