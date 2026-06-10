from sqlalchemy.exc import OperationalError

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
