from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import crud
from backend.schemas import (
    FarmCreate, FarmUpdate, FarmResponse,
    WeatherReadingBody, WeatherReadingCreate, WeatherReadingResponse, PaginatedWeatherResponse,
    SoilMoistureReadingBody, SoilMoistureReadingCreate, SoilMoistureReadingResponse, PaginatedSoilMoistureResponse, WaterStressResponse
)
from backend.services.water_balance import compute_water_balance
from datetime import datetime, timezone, timedelta
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User

router = APIRouter()

@router.post("/", response_model=FarmResponse)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_farm(db=db, farm=farm, user_id=current_user.id)

@router.get("/{farm_id}", response_model=FarmResponse)
def read_farm(farm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    return db_farm

@router.get("/", response_model=list[FarmResponse])
def read_farms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_farms(db=db, user_id=current_user.id, skip=skip, limit=limit)

@router.delete("/{farm_id}", response_model=FarmResponse)
def delete_farm(farm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    return crud.delete_farm(db=db, farm_id=farm_id)

@router.get("/{farm_id}/weather", response_model=PaginatedWeatherResponse)
def read_weather_readings_by_farm(
    farm_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    results = crud.get_weather_readings_by_farm(
        db=db, farm_id=farm_id, skip=skip, limit=limit,
        start_date=start_date, end_date=end_date,
    )
    total = crud.count_weather_readings_by_farm(
        db=db, farm_id=farm_id, start_date=start_date, end_date=end_date,
    )

    return PaginatedWeatherResponse(total=total, skip=skip, limit=limit, results=[WeatherReadingResponse.model_validate(r) for r in results])

@router.get("/{farm_id}/soil-moisture", response_model=PaginatedSoilMoistureResponse)
def read_soil_moisture_readings_by_farm(
    farm_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    results = crud.get_soil_moisture_readings_by_farm(
        db=db, farm_id=farm_id, skip=skip, limit=limit,
        start_date=start_date, end_date=end_date,
    )
    if results is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    total = crud.count_soil_moisture_readings_by_farm(
        db=db, farm_id=farm_id, start_date=start_date, end_date=end_date,
    )
    return PaginatedSoilMoistureResponse(total=total, skip=skip, limit=limit, results=[SoilMoistureReadingResponse.model_validate(r) for r in results])

@router.get("/{farm_id}/soil-moisture/{reading_id}", response_model=SoilMoistureReadingResponse)
def read_soil_moisture_reading(farm_id: int, reading_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    db_reading = crud.get_soil_moisture_reading(db=db, farm_id=farm_id, reading_id=reading_id)
    if db_reading is None:
        raise HTTPException(status_code=404, detail="Soil moisture reading not found")
    return db_reading

@router.post("/{farm_id}/weather", response_model=WeatherReadingResponse)
def create_weather_reading(farm_id: int, body: WeatherReadingBody, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    weather_reading = WeatherReadingCreate(farm_id=farm_id, **body.model_dump())
    return crud.create_weather_reading(db=db, weather_reading=weather_reading)

@router.post("/{farm_id}/soil-moisture", response_model=SoilMoistureReadingResponse)
def create_soil_moisture_reading(farm_id: int, body: SoilMoistureReadingBody, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    soil_moisture_reading = SoilMoistureReadingCreate(farm_id=farm_id, **body.model_dump())
    return crud.create_soil_moisture_reading(db=db, soil_moisture_reading=soil_moisture_reading)


@router.get("/{farm_id}/water-stress", response_model=WaterStressResponse)
def get_water_stress(
    farm_id: int,
    et0_forecast_mm_per_day: float | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    start_date = datetime.now(timezone.utc) - timedelta(days=7)        
    end_date = datetime.now(timezone.utc)

    weather_readings = crud.get_weather_readings_by_farm(db=db, farm_id=farm_id, skip=0, limit=1000, start_date=start_date, end_date=end_date)
    soil_moisture_reading = crud.get_latest_soil_moisture_reading(db=db, farm_id=farm_id)

    water_stress = compute_water_balance(
        farm=db_farm,
        weather_reading=weather_readings,
        soil_moisture_reading=soil_moisture_reading,
        et0_forecast_mm_per_day=et0_forecast_mm_per_day,
    )
    return water_stress