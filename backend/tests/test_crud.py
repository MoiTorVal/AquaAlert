import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, User
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
def user(db):
    u = User(email="test@example.com", hashed_password="dummy-hashed-pw", name="Test User")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def farm(db, user):
    return crud.create_farm(
        db,
        FarmCreate(
            name="Test Farm",
            location="Test Location",
            crop_type="tomato",
            field_capacity_pct=30,
            wilting_point_pct=15,
            root_depth_cm=60,
        ),
        user_id=user.id,
    )


# ── farm CRUD ────────────────────────────────────────────────────────────────


def test_create_farm(db, user):
    result = crud.create_farm(
        db,
        FarmCreate(name="My Farm"),
        user_id=user.id,
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


def test_get_farms_by_user(db, user):
    crud.create_farm(db, FarmCreate(name="Farm A"), user_id=user.id)
    crud.create_farm(db, FarmCreate(name="Farm B"), user_id=user.id)
    results = crud.get_farms(db, user_id=user.id)
    assert len(results) == 2


def test_get_farms_only_returns_own_user(db):
    u1 = User(email="u1@example.com", hashed_password="dummy", name="U1")
    u2 = User(email="u2@example.com", hashed_password="dummy", name="U2")
    db.add_all([u1, u2])
    db.commit()
    crud.create_farm(db, FarmCreate(name="Farm A"), user_id=u1.id)
    crud.create_farm(db, FarmCreate(name="Farm B"), user_id=u2.id)
    results = crud.get_farms(db, user_id=u1.id)
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





def test_get_latest_soil_moisture_reading(db, farm):
    crud.create_soil_moisture_reading(db, make_soil(farm.id, moisture_pct=20.0, offset_days=0))
    crud.create_soil_moisture_reading(db, make_soil(farm.id, moisture_pct=28.0, offset_days=1))
    result = crud.get_latest_soil_moisture_reading(db, farm.id)
    assert float(result.soil_moisture_pct) == 28.0  # most recent


# ── additional coverage ──────────────────────────────────────────────────────


def test_get_weather_reading_by_id(db, farm):
    created = crud.create_weather_reading(db, make_weather(farm.id))
    result = crud.get_weather_reading(db, created.id)
    assert result is not None
    assert result.id == created.id


def test_get_weather_reading_not_found(db):
    result = crud.get_weather_reading(db, 9999)
    assert result is None


def test_get_soil_moisture_reading_by_id(db, farm):
    created = crud.create_soil_moisture_reading(db, make_soil(farm.id))
    result = crud.get_soil_moisture_reading(db, farm_id=farm.id, reading_id=created.id)
    assert result is not None
    assert result.id == created.id


def test_get_soil_moisture_reading_wrong_farm_returns_none(db, farm):
    created = crud.create_soil_moisture_reading(db, make_soil(farm.id))
    result = crud.get_soil_moisture_reading(db, farm_id=9999, reading_id=created.id)
    assert result is None


def test_count_weather_readings_by_farm(db, farm):
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=0))
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=1))
    count = crud.count_weather_readings_by_farm(db, farm.id)
    assert count == 2


def test_count_weather_readings_date_filter(db, farm):
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=0))   # June 1
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=5))   # June 6
    crud.create_weather_reading(db, make_weather(farm.id, offset_days=10))  # June 11
    count = crud.count_weather_readings_by_farm(
        db, farm.id,
        start_date=datetime(2026, 6, 4, tzinfo=timezone.utc),
        end_date=datetime(2026, 6, 8, tzinfo=timezone.utc),
    )
    assert count == 1  # only June 6


def test_count_soil_moisture_readings_by_farm(db, farm):
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=0))
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=1))
    count = crud.count_soil_moisture_readings_by_farm(db, farm.id)
    assert count == 2


def test_count_soil_moisture_readings_date_filter(db, farm):
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=0))   # June 1
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=5))   # June 6
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=10))  # June 11
    count = crud.count_soil_moisture_readings_by_farm(
        db, farm.id,
        start_date=datetime(2026, 6, 4, tzinfo=timezone.utc),
        end_date=datetime(2026, 6, 8, tzinfo=timezone.utc),
    )
    assert count == 1  # only June 6


def test_soil_moisture_date_filter(db, farm):
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=0))   # June 1
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=5))   # June 6
    crud.create_soil_moisture_reading(db, make_soil(farm.id, offset_days=10))  # June 11
    results = crud.get_soil_moisture_readings_by_farm(
        db,
        farm.id,
        start_date=datetime(2026, 6, 4, tzinfo=timezone.utc),
        end_date=datetime(2026, 6, 8, tzinfo=timezone.utc),
    )
    assert len(results) == 1  # only June 6


def test_get_farms_pagination(db, user):
    for i in range(5):
        crud.create_farm(db, FarmCreate(name=f"Farm {i}"), user_id=user.id)
    results = crud.get_farms(db, user_id=user.id, skip=2, limit=2)
    assert len(results) == 2
