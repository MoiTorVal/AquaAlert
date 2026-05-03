import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

import backend.database as db_module
from backend.main import app
from backend.database import get_db
from backend.models import User
from backend.auth import create_access_token
from backend import crud
from backend.schemas import FarmCreate

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def pg_engine():
    with PostgresContainer("postgis/postgis:16-3.4") as pg:
        url = pg.get_connection_url().replace("postgresql://", "postgresql+psycopg2://", 1)
        engine = create_engine(url)

        _orig = db_module.DATABASE_URL
        db_module.DATABASE_URL = url
        try:
            cfg = Config(os.path.join(_PROJECT_ROOT, "alembic.ini"))
            command.upgrade(cfg, "head")
        finally:
            db_module.DATABASE_URL = _orig

        yield engine
        engine.dispose()


@pytest.fixture
def db(pg_engine):
    connection = pg_engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    trans.rollback()
    connection.close()


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
