from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional
from datetime import datetime, date
from backend.enums import SoilTexture, StressSeverity

class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    area_hectares: Optional[float] = None
    crop_type: Optional[str] = None
    root_depth_cm: Optional[float] = None
    growth_stage: Optional[str] = None
    planting_date: Optional[date] = None
    field_capacity_pct: Optional[float] = None
    wilting_point_pct: Optional[float] = None
    soil_type: Optional[SoilTexture] = None
    harvest_date: Optional[date] = None
    field_polygon: Optional[str] = None
    
class FarmUpdate(FarmBase):
    name: Optional[str] = None
class FarmCreate(FarmBase):
    pass
class FarmResponse(FarmBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class WeatherReadingCreate(BaseModel):
    farm_id: int
    recorded_at: datetime
    location: str
    temperature_c: float
    humidity_pct: float
    description: str
    rainfall_mm: float
    wind_speed_kph: float
    
class WeatherReadingResponse(WeatherReadingCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PaginatedWeatherResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[WeatherReadingResponse]

class ETReadingCreate(BaseModel):
    farm_id: int
    reading_date: date 
    et_mm: float
    source: str

class ETReadingResponse(ETReadingCreate):
    id: int
    fetched_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None

    model_config = ConfigDict(from_attributes=True)

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class AquaCropOutputBase(BaseModel):
    depletion_mm: Decimal | None 
    root_zone_moisture_pct: Decimal | None
    severity: StressSeverity | None
    days_to_stress: int | None
    paw_mm: Decimal | None
    raw_threshold_mm: Decimal | None
    
class AquaCropOutputRead(AquaCropOutputBase):
    id: int
    farm_id: int
    run_date: Optional[datetime] = None
    

    model_config = ConfigDict(from_attributes=True)