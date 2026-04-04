import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, Agronomist
from backend import crud
from backend.schemas import FarmCreate, WeatherReadingCreate, SoilMoistureReadingCreate


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def agronomist(db):
    ag = Agronomist(name="Test Agronomist", email="test@example.com")
    db.add(ag)
    db.commit()
    db.refresh(ag)
    return ag


@pytest.fixture
def farm(db, agronomist):
    return crud.create_farm(
        db,
        FarmCreate(
            name="Test Farm",
            location="Test Location",
            agronomist_id=agronomist.id,
            crop_type="tomato",
            field_capacity_pct=30,
            wilting_point_pct=15,
            root_depth_cm=60,
        ),
    )


# ── farm CRUD ────────────────────────────────────────────────────────────────


def test_create_farm(db, agronomist):
    result = crud.create_farm(
        db,
        FarmCreate(
            name="My Farm",
            agronomist_id=agronomist.id,
        ),
    )
    assert result.id is not None
    assert result.name == "My Farm"


def test_get_farm(db, farm):
    result = crud.get_farm(db, farm.id)
    assert result.id == farm.id
    assert result.name == farm.name


def test_get_farm_not_found(db):
    result = crud.get_farm(db, 9999)
    assert result is None


def test_get_farms_by_agronomist(db, agronomist):
    crud.create_farm(db, FarmCreate(name="Farm A", agronomist_id=agronomist.id))
    crud.create_farm(db, FarmCreate(name="Farm B", agronomist_id=agronomist.id))
    results = crud.get_farms(db, agronomist_id=agronomist.id)
    assert len(results) == 2


def test_get_farms_only_returns_own_agronomist(db):
    ag1 = Agronomist(name="Ag1", email="ag1@example.com")
    ag2 = Agronomist(name="Ag2", email="ag2@example.com")
    db.add_all([ag1, ag2])
    db.commit()
    crud.create_farm(db, FarmCreate(name="Farm A", agronomist_id=ag1.id))
    crud.create_farm(db, FarmCreate(name="Farm B", agronomist_id=ag2.id))
    results = crud.get_farms(db, agronomist_id=ag1.id)
    assert len(results) == 1
    assert results[0].name == "Farm A"


def test_delete_farm(db, farm):
    deleted = crud.delete_farm(db, farm.id)
    assert deleted.id == farm.id
    assert crud.get_farm(db, farm.id) is None


def test_delete_farm_not_found(db):
    result = crud.delete_farm(db, 9999)
    assert result is None


# ── weather reading CRUD ─────────────────────────────────────────────────────


def make_weather(farm_id, offset_days=0):
    return WeatherReadingCreate(
        farm_id=farm_id,
        recorded_at=datetime(2026, 6, 1, tzinfo=timezone.utc) + timedelta(days=offset_days),
        location="Test",
        temperature_c=30,
        humidity_pct=60,
        description="Sunny",
        rainfall_mm=0,
        wind_speed_kph=10,
        et0_mm=5.0,
    )


def test_create_weather_reading(db, farm):
    result = crud.create_weather_reading(db, make_weather(farm.id))
    assert result.id is not None
    assert result.farm_id == farm.id


def test_get_weather_readings_by_farm(db, farm):
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=0))
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=1))
    results = crud.get_weather_readings_by_farm(db, farm.id)
    assert len(results) == 2


def test_get_weather_readings_unknown_farm_returns_none(db):
    result = crud.get_weather_readings_by_farm(db, farm_id=9999)
    assert result is None


def test_weather_readings_date_filter(db, farm):
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=0))   # June 1
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=5))   # June 6
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=10))  # June 11
    results = crud.get_weather_readings_by_farm(
        db,
        farm.id,
        start_date=datetime(2026, 6, 4, tzinfo=timezone.utc),
        end_date=datetime(2026, 6, 8, tzinfo=timezone.utc),
    )
    assert len(results) == 1  # only June 6


# ── soil moisture CRUD ───────────────────────────────────────────────────────


def make_soil(farm_id, moisture_pct=25.0, offset_days=0):
    return SoilMoistureReadingCreate(
        farm_id=farm_id,
        recorded_at=datetime(2026, 6, 1, tzinfo=timezone.utc) + timedelta(days=offset_days),
        soil_moisture_pct=moisture_pct,
    )


def test_create_soil_moisture_reading(db, farm):
    result = crud.create_soil_moisture_reading(db, make_soil(farm.id))
    assert result.id is not None
    assert result.soil_moisture_pct == 25.0


def test_get_soil_moisture_readings_by_farm(db, farm):
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=0))
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=1))
    results = crud.get_soil_moisture_readings_by_farm(db, farm.id)
    assert len(results) == 2


def test_get_soil_moisture_readings_unknown_farm_returns_none(db):
    result = crud.get_soil_moisture_readings_by_farm(db, farm_id=9999)
    assert result is None


def test_get_latest_soil_moisture_reading(db, farm):
    crud.create_soil_moisture_reading(db, make_soil(farm.id, moisture_pct=20.0, offset_days=0))
    crud.create_soil_moisture_reading(db, make_soil(farm.id, moisture_pct=28.0, offset_days=1))
    result = crud.get_latest_soil_moisture_reading(db, farm.id)
    assert float(result.soil_moisture_pct) == 28.0  # most recent
