from decimal import Decimal
from datetime import datetime, date

from sqlalchemy import String, Integer, Numeric, DateTime, Date, Boolean, ForeignKey, UniqueConstraint, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base
from geoalchemy2 import Geography
from backend.enums import SoilTexture, StressSeverity, WaterSource, Locale, Tier, IrrigationSource


def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    locale: Mapped[Locale] = mapped_column(
        SAEnum(Locale, name="locale", values_callable=_enum_values),
        nullable=False,
        server_default=Locale.EN.value,
    )
    is_socially_disadvantaged: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_beginning_farmer: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tier: Mapped[Tier] = mapped_column(
        SAEnum(Tier, name="tier", values_callable=_enum_values),
        nullable=False,
        server_default=Tier.FREE.value,
    )

class WeatherReading(Base):
    __tablename__ = "weather_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    description: Mapped[str | None] = mapped_column(String(255))
    humidity_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    rainfall_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    wind_speed_kph: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))

    __table_args__ = (
        UniqueConstraint("farm_id", "recorded_at", name="uq_weather_farm_recorded"),
    )

class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    area_hectares: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    crop_type: Mapped[str | None] = mapped_column(String(100))
    soil_type: Mapped[SoilTexture | None] = mapped_column(SAEnum(SoilTexture, name="soiltexture"), nullable=True)
    root_depth_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    growth_stage: Mapped[str | None] = mapped_column(String(50))
    planting_date: Mapped[date | None] = mapped_column(Date)
    field_capacity_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    wilting_point_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    field_polygon: Mapped[str | None] = mapped_column(Geography("POLYGON", srid=4326), nullable=True)
    harvest_date: Mapped[date | None] = mapped_column(Date)
    acreage_acres: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    pump_hp: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    pump_lift_ft: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    water_source: Mapped[WaterSource | None] = mapped_column(SAEnum(WaterSource, name="watersource", values_callable=_enum_values))


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class ETReading(Base):
    __tablename__ = "et_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)                                       
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    reading_date: Mapped[date] = mapped_column(Date, nullable=False)                                                     
    et_mm: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)                                        
    source: Mapped[str] = mapped_column(String(50), nullable=False)      
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("farm_id", "reading_date", name="uq_et_farm_date"),                                             
    ) 

class AquaCropOutput(Base):
    __tablename__ = "aquacrop_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    depletion_mm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    root_zone_moisture_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    severity: Mapped[StressSeverity | None] = mapped_column(SAEnum(StressSeverity, name="stressseverity", values_callable=_enum_values))
    days_to_stress: Mapped[int | None] = mapped_column(Integer)
    paw_mm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    raw_threshold_mm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))


    __table_args__ = (
        UniqueConstraint("farm_id", "as_of_date", name="uq_aquacrop_farm_date"),
    )


class IrrigationEvent(Base):
    __tablename__ = "irrigation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    gallons_applied: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    source: Mapped[IrrigationSource] = mapped_column(
        SAEnum(IrrigationSource, name="irrigationsource", values_callable=_enum_values),
        nullable=False,
    )
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WaterSavings(Base):
    __tablename__ = "water_savings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    baseline_gallons: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    actual_gallons: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gallons_saved: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    kwh_saved: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    co2_kg_saved: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("farm_id", "period_start", "period_end", name="uq_water_savings_farm_period"),
    )