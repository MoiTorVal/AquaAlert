from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime, date


class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    area_hectares: Optional[float] = None
    crop_type: Optional[str] = None
    soil_type: Optional[str] = None
    root_depth_cm: Optional[float] = None
    growth_stage: Optional[str] = None
    planting_date: Optional[date] = None
    field_capacity_pct: Optional[float] = None
    wilting_point_pct: Optional[float] = None

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
    et0_mm: Optional[float] = None

class WeatherReadingBody(BaseModel):
    recorded_at: datetime
    location: str
    temperature_c: float
    humidity_pct: float
    description: str
    rainfall_mm: float
    wind_speed_kph: float
    et0_mm: Optional[float] = None

class WeatherReadingResponse(WeatherReadingCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PaginatedWeatherResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[WeatherReadingResponse]

class SoilMoistureReadingCreate(BaseModel):
    farm_id: int
    recorded_at: datetime
    soil_moisture_pct: float

class SoilMoistureReadingBody(BaseModel):
    recorded_at: datetime
    soil_moisture_pct: float


class SoilMoistureReadingResponse(SoilMoistureReadingCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PaginatedSoilMoistureResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[SoilMoistureReadingResponse]

class WaterStressResponse(BaseModel):
    current_depletion_mm: float
    paw_mm: float
    raw_threshold_mm: float
    stress_in_days: Optional[int]                  
    warning: bool
    severity: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

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