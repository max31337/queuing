from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models, schemas, crud
import subprocess
import threading
import sys  # Add this import
from datetime import datetime, timedelta
import time
from multiprocessing import Process
from fastapi.middleware.cors import CORSMiddleware
import schedule  # Add this import
import win32print
from app.crud import end_of_day_processing

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict this to specific domains)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/test", response_model=str)
def test_route():
    return "FastAPI is running correctly!"

@app.post("/manual-input", response_model=schemas.QueueRead)
def add_to_queue(item: schemas.QueueCreate, db: Session = Depends(get_db)):
    queue_entry = crud.create_queue(db, item)

    # Generate and print the receipt
    receipt_text = f"""
    MyBank Express
    ----------------------
    Queue Number: {queue_entry.queue_number}
    Transaction: {queue_entry.type}
    Status: {queue_entry.status}
    Date: {queue_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
    ----------------------
    Please wait for your turn.
    Thank you!
    """

    print_receipt(receipt_text)
    return queue_entry

def print_receipt(receipt_text: str):
    printer_name = "POS58 Printer(3)"  # Replace with your printer's name
    raw_data = receipt_text.encode('utf-8')

    # Send receipt to the printer
    hPrinter = win32print.OpenPrinter(printer_name)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("Queue Receipt", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, raw_data)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)

@app.patch("/queue/{queue_id}", response_model=schemas.QueueRead)
def update_queue_status(queue_id: int, update: schemas.QueueUpdate, db: Session = Depends(get_db)):
    result = crud.update_queue_status(db, queue_id, update.status)
    if result is None:
        raise HTTPException(status_code=404, detail="Queue item not found")

    # Handle skipped status
    if update.status == "skipped":
        queue_entry = db.query(models.QueueEntry).filter(models.QueueEntry.id == queue_id).first()
        if queue_entry:
            queue_entry.timestamp = datetime.utcnow()  # Update timestamp for skipped queues
            db.commit()

    return result

@app.get("/queue/list", response_model=list[schemas.QueueRead])
def get_queue_by_number(queue_number: str = None, db: Session = Depends(get_db)):
    if queue_number:
        return db.query(models.QueueEntry).filter(models.QueueEntry.queue_number == queue_number).all()
    return crud.get_all_queue(db)

@app.get("/queue", response_model=list[schemas.QueueRead])
def get_queue_by_number(queue_number: str, db: Session = Depends(get_db)):
    return db.query(models.QueueEntry).filter(models.QueueEntry.queue_number == queue_number).all()

@app.get("/queue/numbers")
def get_queue_numbers(db: Session = Depends(get_db)):
    waiting = db.query(models.QueueEntry).filter(models.QueueEntry.status == "waiting").all()
    processing = db.query(models.QueueEntry).filter(models.QueueEntry.status == "processing").all()
    done = db.query(models.QueueEntry).filter(models.QueueEntry.status == "done").all()
    return {"waiting": [q.queue_number for q in waiting], "processing": [q.queue_number for q in processing], "done": [q.queue_number for q in done]}

@app.get("/queue/active", response_model=list[schemas.QueueRead])
def get_active_queues(db: Session = Depends(get_db)):
    # Filter only queues with 'waiting' or 'processing' statuses
    active_queues = db.query(models.QueueEntry).filter(
        models.QueueEntry.status.in_(["waiting", "processing"])
    ).order_by(models.QueueEntry.timestamp).all()
    return active_queues

@app.get("/queue/archived", response_model=list[schemas.QueueRead])
def list_archived_queues(page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    offset = (page - 1) * page_size
    archived_queues = (
        db.query(models.QueueEntry)
        .filter(models.QueueEntry.archived == True)
        .order_by(models.QueueEntry.timestamp)
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return archived_queues

@app.get("/queue/skipped", response_model=list[schemas.QueueRead])
def get_skipped_queues(db: Session = Depends(get_db)):
    skipped = db.query(models.QueueEntry).filter(models.QueueEntry.status == "skipped").all()
    return skipped

# Function to run printer.py
def run_printer_script():
    python_executable = sys.executable
    subprocess.run([python_executable, "c:\\Users\\navar\\queuing\\app\\printer.py"])

def archive_done_entries_periodically():
    while True:
        db = SessionLocal()
        try:
            crud.archive_done_entries(db)
        finally:
            db.close()
        time.sleep(60)  # Run every 60 seconds

# Function to run end-of-day processing
def run_end_of_day_processing():
    db = SessionLocal()
    try:
        end_of_day_processing(db)
        print("End-of-day processing completed.")
    except Exception as e:
        print(f"Error during end-of-day processing: {e}")
    finally:
        db.close()

# Schedule the task to run daily at 11:59 PM
def schedule_end_of_day_task():
    schedule.every().day.at("23:59").do(run_end_of_day_processing)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start printer.py in a separate thread when the app starts
@app.on_event("startup")
def startup_event():
    Process(target=run_printer_script, daemon=True).start()
    threading.Thread(target=archive_done_entries_periodically, daemon=True).start()
    threading.Thread(target=schedule_end_of_day_task, daemon=True).start()
