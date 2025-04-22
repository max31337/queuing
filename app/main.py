from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models, schemas, crud

models.Base.metadata.create_all(bind=engine)  # For local dev only

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/queue", response_model=schemas.QueueRead)
def add_to_queue(item: schemas.QueueCreate, db: Session = Depends(get_db)):
    return crud.create_queue(db, item)

@app.get("/queue", response_model=list[schemas.QueueRead])
def list_queue(db: Session = Depends(get_db)):
    return crud.get_all_queue(db)
