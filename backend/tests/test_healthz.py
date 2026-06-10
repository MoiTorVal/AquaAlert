import logging
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

import backend.database as db_module
import backend.main as main_module
from backend.database import get_db
from backend.main import app


def test_healthz_ok(unauthed_client):
    response = unauthed_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_healthz_db_down(unauthed_client):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    try:
        response = unauthed_client.get("/healthz")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down"}


# ── lifespan ─────────────────────────────────────────────────────────────────


def test_lifespan_verifies_db_and_runs_scheduler(monkeypatch, caplog):
    fake_engine = MagicMock()
    monkeypatch.setattr(main_module, "engine", fake_engine)
    monkeypatch.setattr(main_module.settings, "scheduler_enabled", True)
    started, stopped = [], []
    monkeypatch.setattr(main_module, "start_scheduler", lambda: started.append(True))
    monkeypatch.setattr(main_module, "shutdown_scheduler", lambda: stopped.append(True))

    with caplog.at_level(logging.INFO, logger="backend.main"):
        # entering/exiting the TestClient context runs startup and shutdown
        with TestClient(app):
            pass

    assert "Database connection verified on startup" in caplog.text
    fake_engine.connect.return_value.__enter__.return_value.execute.assert_called_once()
    assert started == [True]
    assert stopped == [True]


def test_lifespan_db_failure_logged_but_app_starts(monkeypatch, caplog):
    fake_engine = MagicMock()
    fake_engine.connect.side_effect = RuntimeError("db down")
    monkeypatch.setattr(main_module, "engine", fake_engine)

    with caplog.at_level(logging.ERROR, logger="backend.main"):
        with TestClient(app):
            pass

    assert "Error connecting to the database on startup" in caplog.text


# ── get_db ───────────────────────────────────────────────────────────────────


def test_get_db_yields_session_and_closes_it(monkeypatch):
    fake_session = MagicMock()
    monkeypatch.setattr(db_module, "SessionLocal", lambda: fake_session)

    gen = get_db()
    assert next(gen) is fake_session
    fake_session.close.assert_not_called()
    gen.close()  # what FastAPI does once the request finishes
    fake_session.close.assert_called_once()
