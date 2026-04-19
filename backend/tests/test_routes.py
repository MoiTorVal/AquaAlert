import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db
from backend.models import Base, User
from backend.auth import create_access_token
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
def user(db):
    u = User(email="test@example.com", hashed_password="dummy", name="Test User")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def client(db, user):
    app.dependency_overrides[get_db] = lambda: db
    token = create_access_token({"sub": str(user.id)})
    c = TestClient(app)
    c.cookies.set("access_token", token)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


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


# ── farm routes ──────────────────────────────────────────────────────────────


def test_create_farm_route(client):
    response = client.post("/farms/", json={"name": "New Farm", "crop_type": "wheat"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Farm"


def test_create_farm_unauthenticated(unauthed_client):
    response = unauthed_client.post("/farms/", json={"name": "New Farm"})
    assert response.status_code == 401


def test_get_farm_route(client, farm):
    response = client.get(f"/farms/{farm.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Farm"


def test_get_farm_not_found_route(client):
    response = client.get("/farms/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_get_farm_other_user_returns_404(client, db):
    other = User(email="other@example.com", hashed_password="dummy", name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)
    other_farm = crud.create_farm(db, FarmCreate(name="Other Farm"), user_id=other.id)
    response = client.get(f"/farms/{other_farm.id}")
    assert response.status_code == 404


def test_get_farms_route(client, farm):
    response = client.get("/farms/")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_farms_only_returns_own(client, db, user):
    other = User(email="other@example.com", hashed_password="dummy", name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)
    crud.create_farm(db, FarmCreate(name="My Farm"), user_id=user.id)
    crud.create_farm(db, FarmCreate(name="Other Farm"), user_id=other.id)
    response = client.get("/farms/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "My Farm"


def test_delete_farm_route(client, farm):
    response = client.delete(f"/farms/{farm.id}")
    assert response.status_code == 200
    assert client.get(f"/farms/{farm.id}").status_code == 404


def test_delete_farm_not_found_route(client):
    response = client.delete("/farms/9999")
    assert response.status_code == 404


def test_delete_farm_other_user_returns_404(client, db):
    other = User(email="other@example.com", hashed_password="dummy", name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)
    other_farm = crud.create_farm(db, FarmCreate(name="Other Farm"), user_id=other.id)
    response = client.delete(f"/farms/{other_farm.id}")
    assert response.status_code == 404


# ── update farm routes ───────────────────────────────────────────────────────


def test_update_farm_route(client, farm):
    response = client.put(f"/farms/{farm.id}", json={"name": "Updated Farm"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Farm"
    assert response.json()["crop_type"] == "tomato"


def test_update_farm_not_found_route(client):
    response = client.put("/farms/9999", json={"name": "Ghost"})
    assert response.status_code == 404


def test_update_farm_other_user_returns_404(client, db):
    other = User(email="other@example.com", hashed_password="dummy", name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)
    other_farm = crud.create_farm(db, FarmCreate(name="Other Farm"), user_id=other.id)
    response = client.put(f"/farms/{other_farm.id}", json={"name": "Hacked"})
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


def test_get_soil_moisture_readings_unknown_farm_route(client):
    response = client.get("/farms/9999/soil-moisture")
    assert response.status_code == 404


def test_get_soil_moisture_reading_by_id_route(client, farm):
    post_resp = client.post(f"/farms/{farm.id}/soil-moisture", json={
        "recorded_at": "2026-06-01T00:00:00Z",
        "soil_moisture_pct": 25.0,
    })
    reading_id = post_resp.json()["id"]
    response = client.get(f"/farms/{farm.id}/soil-moisture/{reading_id}")
    assert response.status_code == 200
    assert response.json()["soil_moisture_pct"] == 25.0


def test_get_soil_moisture_reading_not_found_route(client, farm):
    response = client.get(f"/farms/{farm.id}/soil-moisture/9999")
    assert response.status_code == 404


def test_get_soil_moisture_reading_other_user_returns_404(client, db):
    other = User(email="other@example.com", hashed_password="dummy", name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)
    other_farm = crud.create_farm(db, FarmCreate(name="Other Farm"), user_id=other.id)
    response = client.get(f"/farms/{other_farm.id}/soil-moisture/1")
    assert response.status_code == 404


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


def test_water_stress_with_et0_forecast_route(client, farm):
    response = client.get(f"/farms/{farm.id}/water-stress", params={"et0_forecast_mm_per_day": 5.0})
    assert response.status_code == 200
    data = response.json()
    assert data["stress_in_days"] is not None
