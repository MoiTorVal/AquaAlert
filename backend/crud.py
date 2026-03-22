from backend import models
from backend.schemas import FarmCreate
from sqlalchemy.orm import Session

def create_farm(db: Session, farm: FarmCreate):
    db_farm = models.Farm(**farm.model_dump())
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm

def get_farm(db: Session, farm_id: int):
    return db.query(models.Farm).filter(models.Farm.id == farm_id).first()

def get_farms(db: Session, agronomist_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Farm).filter(models.Farm.agronomist_id == agronomist_id).offset(skip).limit(limit).all()

def delete_farm(db: Session, farm_id: int):
    db_farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()
    if db_farm:
        db.delete(db_farm)
        db.commit()
    return db_farm