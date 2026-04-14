from decimal import Decimal
from datetime import datetime, date, timezone

from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


default = lambda: datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=default)


class WeatherReading(Base):
    __tablename__ = "weather_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    description: Mapped[str | None] = mapped_column(String(255))
    humidity_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    rainfall_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    wind_speed_kph: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    et0_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))

    __table_args__ = (
        UniqueConstraint("farm_id", "recorded_at", name="uq_weather_farm_recorded"),
    )


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=default)
    area_hectares: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    crop_type: Mapped[str | None] = mapped_column(String(100))
    soil_type: Mapped[str | None] = mapped_column(String(100))
    root_depth_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    growth_stage: Mapped[str | None] = mapped_column(String(50))
    planting_date: Mapped[date | None] = mapped_column(Date)
    field_capacity_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    wilting_point_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))


class SoilMoistureReading(Base):
    __tablename__ = "soil_moisture_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    soil_moisture_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))


class IrrigationRecommendation(Base):
    __tablename__ = "irrigation_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    weather_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("weather_readings.id"))
    recommended_at: Mapped[datetime | None] = mapped_column(DateTime, default=default)
    water_amount_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    duration_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    method: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")