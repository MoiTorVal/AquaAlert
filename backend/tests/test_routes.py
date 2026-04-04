import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.routers.farms import get_db
from backend.models import Base, Agronomist
from backend import crud
from backend.schemas import FarmCreate


# ── test database setup ──────────────────────────────────────────────────────


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


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


# ── farm routes ──────────────────────────────────────────────────────────────


def test_create_farm_route(client, agronomist):
    response = client.post("/farms/", json={
        "name": "New Farm",
        "agronomist_id": agronomist.id,
        "crop_type": "wheat",
    })
    assert response.status_code == 200
    assert response.json()["name"] == "New Farm"


def test_get_farm_route(client, farm):
    response = client.get(f"/farms/{farm.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Farm"


def test_get_farm_not_found_route(client):
    response = client.get("/farms/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_get_farms_route(client, agronomist, farm):
    response = client.get("/farms/", params={"agronomist_id": agronomist.id})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_farm_route(client, farm):
    response = client.delete(f"/farms/{farm.id}")
    assert response.status_code == 200
    assert client.get(f"/farms/{farm.id}").status_code == 404


def test_delete_farm_not_found_route(client):
    response = client.delete("/farms/9999")
    assert response.status_code == 404


# ── weather routes ───────────────────────────────────────────────────────────


def test_create_weather_reading_route(client, farm):
    response = client.post(f"/farms/{farm.id}/weather", json={
        "recorded_at": "2026-06-01T00:00:00Z",
        "location": "Test",
        "temperature_c": 30,
        "humidity_pct": 60,
        "description": "Sunny",
        "rainfall_mm": 0,
        "wind_speed_kph": 10,
        "et0_mm": 5.0,
    })
    assert response.status_code == 200
    assert response.json()["farm_id"] == farm.id


def test_create_weather_reading_unknown_farm(client):
    response = client.post("/farms/9999/weather", json={
        "recorded_at": "2026-06-01T00:00:00Z",
        "location": "Test",
        "temperature_c": 30,
        "humidity_pct": 60,
        "description": "Sunny",
        "rainfall_mm": 0,
        "wind_speed_kph": 10,
    })
    assert response.status_code == 404


def test_get_weather_readings_route(client, farm):
    client.post(f"/farms/{farm.id}/weather", json={
        "recorded_at": "2026-06-01T00:00:00Z",
        "location": "Test",
        "temperature_c": 30,
        "humidity_pct": 60,
        "description": "Sunny",
        "rainfall_mm": 0,
        "wind_speed_kph": 10,
    })
    response = client.get(f"/farms/{farm.id}/weather")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_get_weather_readings_unknown_farm(client):
    response = client.get("/farms/9999/weather")
    assert response.status_code == 404


# ── soil moisture routes ─────────────────────────────────────────────────────


def test_create_soil_moisture_route(client, farm):
    response = client.post(f"/farms/{farm.id}/soil-moisture", json={
        "recorded_at": "2026-06-01T00:00:00Z",
        "soil_moisture_pct": 25.0,
    })
    assert response.status_code == 200
    assert response.json()["farm_id"] == farm.id


def test_create_soil_moisture_unknown_farm(client):
    response = client.post("/farms/9999/soil-moisture", json={
        "recorded_at": "2026-06-01T00:00:00Z",
        "soil_moisture_pct": 25.0,
    })
    assert response.status_code == 404


def test_get_soil_moisture_readings_route(client, farm):
    client.post(f"/farms/{farm.id}/soil-moisture", json={
        "recorded_at": "2026-06-01T00:00:00Z",
        "soil_moisture_pct": 25.0,
    })
    response = client.get(f"/farms/{farm.id}/soil-moisture")
    assert response.status_code == 200
    assert response.json()["total"] == 1


# ── water stress route ───────────────────────────────────────────────────────


def test_water_stress_route(client, farm):
    response = client.get(f"/farms/{farm.id}/water-stress")
    assert response.status_code == 200
    data = response.json()
    assert "current_depletion_mm" in data
    assert "severity" in data
    assert "warning" in data


def test_water_stress_unknown_farm(client):
    response = client.get("/farms/9999/water-stress")
    assert response.status_code == 404


