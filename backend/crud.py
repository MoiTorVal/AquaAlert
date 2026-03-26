from backend import models
from backend.schemas import FarmCreate, SoilMoistureReadingCreate, WeatherReadingCreate
from sqlalchemy.orm import Session
from datetime import datetime

# CRUD operations for farms
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


def create_weather_reading(db: Session, weather_reading: WeatherReadingCreate):
    db_weather_reading = models.WeatherReading(**weather_reading.model_dump())
    db.add(db_weather_reading)
    db.commit()
    db.refresh(db_weather_reading)
    return db_weather_reading

def get_weather_reading(db: Session, weather_reading_id: int):
    return db.query(models.WeatherReading).filter(models.WeatherReading.id == weather_reading_id).first()

def _weather_readings_base_query(db: Session, farm_id: int, start_date: datetime | None, end_date: datetime | None):
    query = db.query(models.WeatherReading).filter(models.WeatherReading.farm_id == farm_id)
    if start_date:
        query = query.filter(models.WeatherReading.recorded_at >= start_date)
    if end_date:
        query = query.filter(models.WeatherReading.recorded_at <= end_date)
    return query


def get_weather_readings_by_farm(
    db: Session,
    farm_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list | None:
    if not db.query(models.Farm).filter(models.Farm.id == farm_id).first():
        return None
    return (
        _weather_readings_base_query(db, farm_id, start_date, end_date)
        .order_by(models.WeatherReading.recorded_at)
        .offset(skip)
        .limit(limit)
        .all()
    )

def count_weather_readings_by_farm(
    db: Session,
    farm_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> int:
    return _weather_readings_base_query(db, farm_id, start_date, end_date).count()


def create_soil_moisture_reading(db: Session, soil_moisture_reading: SoilMoistureReadingCreate):
    db_soil_moisture_reading = models.SoilMoistureReading(**soil_moisture_reading.model_dump())
    db.add(db_soil_moisture_reading)
    db.commit()
    db.refresh(db_soil_moisture_reading)
    return db_soil_moisture_reading

def get_soil_moisture_reading(db: Session, farm_id: int, reading_id: int):
    return db.query(models.SoilMoistureReading).filter(
        models.SoilMoistureReading.id == reading_id,
        models.SoilMoistureReading.farm_id == farm_id,
    ).first()

def get_soil_moisture_readings_by_farm(
    db: Session,
    farm_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list | None:
    if not db.query(models.Farm).filter(models.Farm.id == farm_id).first():
        return None
    query = db.query(models.SoilMoistureReading).filter(models.SoilMoistureReading.farm_id == farm_id)
    if start_date:
        query = query.filter(models.SoilMoistureReading.recorded_at >= start_date)
    if end_date:
        query = query.filter(models.SoilMoistureReading.recorded_at <= end_date)
    return query.order_by(models.SoilMoistureReading.recorded_at).offset(skip).limit(limit).all()

def count_soil_moisture_readings_by_farm(
    db: Session,
    farm_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> int:
    query = db.query(models.SoilMoistureReading).filter(models.SoilMoistureReading.farm_id == farm_id)
    if start_date:
        query = query.filter(models.SoilMoistureReading.recorded_at >= start_date)
    if end_date:
        query = query.filter(models.SoilMoistureReading.recorded_at <= end_date)
    return query.count()
