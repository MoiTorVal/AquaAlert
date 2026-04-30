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


# ── auth routes ──────────────────────────────────────────────────────────────


def test_signup(unauthed_client):
    response = unauthed_client.post("/auth/signup", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "secret123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Account created"
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice"
    assert "id" in data["user"]
    assert "access_token" not in data


def test_signup_duplicate_email(unauthed_client, user):
    response = unauthed_client.post("/auth/signup", json={
        "name": "Dupe",
        "email": "test@example.com",
        "password": "secret123",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_success(db, unauthed_client):
    from backend.auth import hash_password
    from backend.models import User as UserModel
    u = UserModel(email="login@example.com", hashed_password=hash_password("correctpass"), name="Login User")
    db.add(u)
    db.commit()

    response = unauthed_client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "correctpass",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "login@example.com"
    assert "id" in data["user"]
    assert "access_token" not in data


def test_login_wrong_password(db, unauthed_client):
    from backend.auth import hash_password
    from backend.models import User as UserModel
    u = UserModel(email="wp@example.com", hashed_password=hash_password("correctpass"), name="WP User")
    db.add(u)
    db.commit()

    response = unauthed_client.post("/auth/login", json={
        "email": "wp@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(unauthed_client):
    response = unauthed_client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "irrelevant",
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_forgot_password_registered_email(unauthed_client, user):
    response = unauthed_client.post("/auth/forgot-password", json={
        "email": "test@example.com",
    })
    assert response.status_code == 200
    assert "reset link" in response.json()["message"]


def test_forgot_password_unregistered_email(unauthed_client):
    response = unauthed_client.post("/auth/forgot-password", json={
        "email": "ghost@example.com",
    })
    assert response.status_code == 200
    assert "reset link" in response.json()["message"]


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




def test_get_weather_readings_unknown_farm(client):
    response = client.get("/farms/9999/weather")
    assert response.status_code == 404

