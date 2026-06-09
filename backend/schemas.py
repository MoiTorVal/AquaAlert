from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from backend.enums import SoilTexture, StressSeverity, WaterSource, Locale, Tier, IrrigationSource

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
    water_source: Optional[WaterSource] = None
    pump_hp: Optional[float] = None
    pump_lift_ft: Optional[float] = None
    acreage_acres: Optional[float] = None

class FarmUpdate(FarmBase):
    name: Optional[str] = None
class FarmCreate(FarmBase):
    pass
class FarmResponse(FarmBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("field_polygon", mode="before")
    @classmethod
    def _polygon_to_wkt(cls, v):
        if isinstance(v, WKBElement):
            return to_shape(v).wkt
        return v

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
    locale: Locale
    tier: Tier
    is_socially_disadvantaged: Optional[bool] = None
    is_beginning_farmer: Optional[bool] = None

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
    as_of_date: date
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


class IrrigationEventCreate(BaseModel):
    event_date: date
    gallons_applied: Decimal


class IrrigationEventResponse(BaseModel):
    id: int
    farm_id: int
    event_date: date
    gallons_applied: Decimal
    source: IrrigationSource
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedIrrigationEventResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[IrrigationEventResponse]


class BaselineIrrigationCreate(BaseModel):
    gallons_per_week_estimate: Decimal = Field(gt=0)


class BaselineIrrigationResponse(BaseModel):
    id: int
    farm_id: int
    gallons_per_week_estimate: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedBaselineIrrigationResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[BaselineIrrigationResponse]


class WaterSavingsResponse(BaseModel):
    id: int
    farm_id: int
    period_start: date
    period_end: date
    baseline_gallons: Decimal
    actual_gallons: Decimal
    gallons_saved: Decimal
    kwh_saved: Decimal
    co2_kg_saved: Decimal
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedWaterSavingsResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[WaterSavingsResponse]