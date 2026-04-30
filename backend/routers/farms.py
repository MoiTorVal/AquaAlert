from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import crud
from backend.schemas import (
    FarmCreate, FarmUpdate, FarmResponse,
    WeatherReadingResponse, PaginatedWeatherResponse 
)
from datetime import datetime, timezone, timedelta
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User

router = APIRouter()


def _validate_farm_ownership(db: Session, farm_id: int, user_id: int):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != user_id:
        raise HTTPException(status_code=404, detail="Farm not found")
    return db_farm

@router.post("/", response_model=FarmResponse)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_farm(db=db, farm=farm, user_id=current_user.id)

@router.get("/{farm_id}", response_model=FarmResponse)
def read_farm(farm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    return db_farm

@router.get("/", response_model=list[FarmResponse])
def read_farms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_farms(db=db, user_id=current_user.id, skip=skip, limit=limit)

@router.delete("/{farm_id}", response_model=FarmResponse)
def delete_farm(farm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    return crud.delete_farm(db=db, farm_id=farm_id)

@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, farm_update: FarmUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    return crud.update_farm(db=db, farm_id=farm_id, farm_update=farm_update)


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
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    
    results = crud.get_weather_readings_by_farm(
        db=db, farm_id=farm_id, skip=skip, limit=limit,
        start_date=start_date, end_date=end_date,
    )
    total = crud.count_weather_readings_by_farm(
        db=db, farm_id=farm_id, start_date=start_date, end_date=end_date,
    )

    return PaginatedWeatherResponse(total=total, skip=skip, limit=limit, results=[WeatherReadingResponse.model_validate(r) for r in results])

