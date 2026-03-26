from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy import ForeignKey
from datetime import datetime, timezone, date
from backend.database import Base

default=lambda: datetime.now(timezone.utc)

class Agronomist(Base):
    __tablename__ = "agronomists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime, default=default)

class WeatherReading(Base):
    __tablename__ = "weather_readings"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    location = Column(String(255))
    temperature_c = Column(Numeric(5, 2))
    description = Column(String(255))
    humidity_pct = Column(Numeric(5, 2))
    rainfall_mm = Column(Numeric(8, 2))
    wind_speed_kph = Column(Numeric(6, 2))
    et0_mm = Column(Numeric(8, 2))


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(255))
    created_at = Column(DateTime, default=default)
    agronomist_id = Column(Integer, ForeignKey("agronomists.id"), nullable=False)
    area_hectares = Column(Numeric(10, 2))
    crop_type = Column(String(100))
    soil_type = Column(String(100))
    root_depth_cm = Column(Numeric(5, 2))
    growth_stage = Column(String(50))
    planting_date = Column(date)
    field_capacity_pct = Column(Numeric(5, 2))
    wilting_point_pct = Column(Numeric(5, 2))

class SoilMoistureReading(Base):
    __tablename__ = "soil_moisture_readings"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    soil_moisture_pct = Column(Numeric(5, 2))

class IrrigationRecommendation(Base):
    __tablename__ = "irrigation_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    weather_id = Column(Integer, ForeignKey("weather_readings.id"))
    recommended_at = Column(DateTime, default=default)
    water_amount_mm = Column(Numeric(8, 2), nullable=False)
    duration_hours = Column(Numeric(5, 2))
    method = Column(String(50))
    notes = Column(String(500))
    status = Column(String(20), default='pending')
  
