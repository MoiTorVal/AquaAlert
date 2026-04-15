import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from datetime import timedelta
import jwt

from backend.main import app
from backend.database import get_db
from backend.models import Base, User
from backend.auth import hash_password, create_access_token, SECRET_KEY, ALGORITHM


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
def existing_user(db):
    u = User(email="existing@example.com", hashed_password=hash_password("correctpass"), name="Existing")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ── signup ───────────────────────────────────────────────────────────────────


def test_signup(client):
    response = client.post("/auth/signup", json={
        "email": "new@example.com",
        "password": "securepass",
        "name": "New User",
    })
    assert response.status_code == 201
    assert response.json()["message"] == "Account created"
    assert "access_token" in response.cookies


def test_signup_duplicate_email(client, existing_user):
    response = client.post("/auth/signup", json={
        "email": "existing@example.com",
        "password": "anypass",
        "name": "Duplicate",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_signup_invalid_email(client):
    response = client.post("/auth/signup", json={
        "email": "not-an-email",
        "password": "securepass",
        "name": "Bad Email",
    })
    assert response.status_code == 422


# ── login ────────────────────────────────────────────────────────────────────


def test_login(client, existing_user):
    response = client.post("/auth/login", json={
        "email": "existing@example.com",
        "password": "correctpass",
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"
    assert "access_token" in response.cookies


def test_login_wrong_password(client, existing_user):
    response = client.post("/auth/login", json={
        "email": "existing@example.com",
        "password": "wrongpass",
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(client):
    response = client.post("/auth/login", json={
        "email": "ghost@example.com",
        "password": "anypass",
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


# ── forgot password ──────────────────────────────────────────────────────────


def test_forgot_password_known_email(client, existing_user):
    response = client.post("/auth/forgot-password", json={"email": "existing@example.com"})
    assert response.status_code == 200
    assert "message" in response.json()


def test_forgot_password_unknown_email(client):
    response = client.post("/auth/forgot-password", json={"email": "ghost@example.com"})
    assert response.status_code == 200
    assert "message" in response.json()


def test_forgot_password_same_response_for_known_and_unknown(client, existing_user):
    known = client.post("/auth/forgot-password", json={"email": "existing@example.com"})
    unknown = client.post("/auth/forgot-password", json={"email": "ghost@example.com"})
    assert known.json()["message"] == unknown.json()["message"]


# ── invalid token ─────────────────────────────────────────────────────────────


def test_invalid_token_rejected(client):
    response = client.get("/farms/", cookies={"access_token": "thisistotallynotavalidtoken"})
    assert response.status_code == 401


def test_missing_token_rejected(client):
    response = client.get("/farms/")
    assert response.status_code == 401


def test_expired_token_rejected(client):
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    response = client.get("/farms/", cookies={"access_token": token})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_token_missing_sub_rejected(client):
    token = jwt.encode({"exp": 9999999999}, SECRET_KEY, algorithm=ALGORITHM)
    response = client.get("/farms/", cookies={"access_token": token})
    assert response.status_code == 401


def test_token_non_int_sub_rejected(client):
    token = create_access_token({"sub": "notanint"})
    response = client.get("/farms/", cookies={"access_token": token})
    assert response.status_code == 401


def test_token_deleted_user_rejected(client):
    token = create_access_token({"sub": "99999"})
    response = client.get("/farms/", cookies={"access_token": token})
    assert response.status_code == 401
