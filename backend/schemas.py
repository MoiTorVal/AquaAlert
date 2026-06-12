import re
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely import wkt as shapely_wkt
from shapely.errors import ShapelyError
from backend.enums import (
    SoilTexture, StressSeverity, WaterSource, Locale, Tier, IrrigationSource,
    AlertChannel, AlertFeedback,
)

# E.164 — what Twilio sends in webhook From and expects in To.
_E164_RE = re.compile(r"^\+[1-9]\d{1,14}$")

# Leaflet-draw field boundaries run tens of vertices; this only blocks
# abusive payloads that would bloat the DB row and the OpenET request body.
MAX_POLYGON_VERTICES = 1000


def _password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    # bcrypt hashes only the first 72 bytes — reject instead of silently
    # ignoring everything past the limit.
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes")
    return v

class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
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

class FarmWrite(FarmBase):
    """Write-side validation only — FarmResponse must not re-parse trusted
    DB geometry on every read (and must never 500 on legacy rows)."""

    @field_validator("field_polygon")
    @classmethod
    def _validate_polygon(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            geom = shapely_wkt.loads(v)
        except ShapelyError as exc:
            raise ValueError("field_polygon must be valid WKT") from exc
        if geom.geom_type != "Polygon":
            raise ValueError("field_polygon must be a POLYGON")
        if not geom.is_valid:
            raise ValueError("field_polygon must be a valid polygon (no self-intersections)")
        vertex_count = len(geom.exterior.coords) + sum(len(ring.coords) for ring in geom.interiors)
        if vertex_count > MAX_POLYGON_VERTICES:
            raise ValueError(f"field_polygon exceeds {MAX_POLYGON_VERTICES} vertices")
        return v

class FarmUpdate(FarmWrite):
    name: Optional[str] = None
class FarmCreate(FarmWrite):
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
    
# Not WeatherReadingCreate: scheduler rainfall rows fill only rainfall_mm,
# so every measurement field must serialize as nullable.
class WeatherReadingResponse(BaseModel):
    id: int
    farm_id: int
    recorded_at: datetime
    location: str | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    description: str | None = None
    rainfall_mm: float | None = None
    wind_speed_kph: float | None = None
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

class ETSeriesResponse(BaseModel):
    farm_id: int
    start_date: date
    end_date: date
    as_of: Optional[date]
    results: list[ETReadingResponse]

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _password_strength(v)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    locale: Locale
    tier: Tier
    is_socially_disadvantaged: Optional[bool] = None
    is_beginning_farmer: Optional[bool] = None
    phone_number: Optional[str] = None
    sms_alerts_enabled: bool = False

    model_config = ConfigDict(from_attributes=True)

class UserUpdateRequest(BaseModel):
    """Self-service profile updates. Equity fields are voluntary self-ID —
    always optional, may be set back to null (decline to answer)."""
    locale: Optional[Locale] = None
    is_socially_disadvantaged: Optional[bool] = None
    is_beginning_farmer: Optional[bool] = None
    phone_number: Optional[str] = None
    sms_alerts_enabled: Optional[bool] = None

    @field_validator("phone_number")
    @classmethod
    def _validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not _E164_RE.fullmatch(v):
            raise ValueError("phone_number must be E.164 format, e.g. +15551234567")
        return v


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _password_strength(v)

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


class WaterStressResponse(AquaCropOutputRead):
    """AquaCrop result + stale-data guard fields ("as of [date]" trust signal).

    et_latest_date > et_latest_actual_date means recent days are provisional
    CIMIS gap-fill estimates, not OpenET actuals — UI should say "estimated".
    """
    et_latest_date: Optional[date] = None
    et_latest_actual_date: Optional[date] = None
    et_is_stale: bool


class IrrigationEventCreate(BaseModel):
    event_date: date
    gallons_applied: Decimal
    # Runtime-mode logs keep what the farmer entered; gallons_applied stays canonical.
    hours_run: Optional[Decimal] = Field(None, gt=0)
    pump_gpm: Optional[Decimal] = Field(None, gt=0)


class IrrigationEventResponse(BaseModel):
    id: int
    farm_id: int
    event_date: date
    gallons_applied: Decimal
    hours_run: Optional[Decimal] = None
    pump_gpm: Optional[Decimal] = None
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


class WaterSavingsBase(BaseModel):
    period_start: date
    period_end: date
    baseline_gallons: Decimal
    actual_gallons: Decimal
    gallons_saved: Decimal
    kwh_saved: Decimal
    co2_kg_saved: Decimal


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


class SavingsTotals(BaseModel):
    baseline_gallons: Decimal
    actual_gallons: Decimal
    gallons_saved: Decimal
    kwh_saved: Decimal
    co2_kg_saved: Decimal


class SavingsSeriesResponse(BaseModel):
    farm_id: int
    start_date: date
    end_date: date
    totals: SavingsTotals
    results: list[WaterSavingsResponse]


class AlertResponse(BaseModel):
    """Alert history row. provider_message_sid is internal — never exposed."""
    id: int
    farm_id: int
    severity: StressSeverity
    as_of_date: date
    days_to_stress: Optional[int] = None
    channel: AlertChannel
    sent_at: datetime
    feedback: Optional[AlertFeedback] = None
    feedback_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedAlertResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[AlertResponse]


class SatelliteScanSummaryResponse(BaseModel):
    """List-endpoint row: stats only — the (large) NDVI grid ships solely via
    the single-scan endpoint so history pages stay cheap."""
    id: int
    farm_id: int
    scan_date: date
    cloud_cover_pct: Decimal | None = None
    mean_ndvi: Decimal | None = None
    max_ndvi: Decimal | None = None
    min_ndvi: Decimal | None = None
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SatelliteScanResponse(SatelliteScanSummaryResponse):
    ndvi_grid: list[list[float | None]] | None = None
    ndvi_grid_bounds: list[list[float]] | None = None


class PaginatedSatelliteScanResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: list[SatelliteScanSummaryResponse]


class RegionalStatsResponse(BaseModel):
    """Public aggregate — no farm-identifiable or equity data, ever."""
    snapshot_date: date
    total_farms: int
    farms_green: int
    farms_yellow: int
    farms_red: int
    total_gallons_saved: Decimal
    total_kwh_saved: Decimal
    total_co2_kg_saved: Decimal
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)