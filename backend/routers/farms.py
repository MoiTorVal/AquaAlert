from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import crud
from backend.schemas import FarmCreate, FarmResponse
from typing import List

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

@router.post("/", response_model=FarmResponse)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db)):
    return crud.create_farm(db=db, farm=farm)

@router.get("/{farm_id}", response_model=FarmResponse)
def read_farm(farm_id: int, db: Session = Depends(get_db)):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return db_farm

@router.get("/", response_model=List[FarmResponse])
def read_farms(agronomist_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_farms(db=db, agronomist_id=agronomist_id, skip=skip, limit=limit)

@router.delete("/{farm_id}", response_model=FarmResponse)
def delete_farm(farm_id: int, db: Session = Depends(get_db)):
    db_farm = crud.delete_farm(db=db, farm_id=farm_id)
    if db_farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return db_farm