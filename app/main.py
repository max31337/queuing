from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models, schemas, crud

app = FastAPI()

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

@app.post("/queue", response_model=schemas.QueueRead)
def add_to_queue(item: schemas.QueueCreate, db: Session = Depends(get_db)):
    return crud.create_queue(db, item)

from fastapi import HTTPException

@app.patch("/queue/{queue_id}", response_model=schemas.QueueRead)
def update_queue_status(queue_id: int, update: schemas.QueueUpdate, db: Session = Depends(get_db)):
    result = crud.update_queue_status(db, queue_id, update.status)
    if result is None:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return result


@app.get("/queue", response_model=list[schemas.QueueRead])
def list_queue(db: Session = Depends(get_db)):
    return crud.get_all_queue(db)
