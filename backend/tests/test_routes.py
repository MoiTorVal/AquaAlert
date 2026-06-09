from datetime import date
from decimal import Decimal

import pytest
from shapely import wkt as shapely_wkt

from backend.models import User, WaterSavings
from backend import crud
from backend.schemas import FarmCreate

POLYGON_WKT = "POLYGON ((-120.5 36.5, -120.4 36.5, -120.4 36.6, -120.5 36.6, -120.5 36.5))"


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


# ── pagination caps ──────────────────────────────────────────────────────────


LIST_PATHS = [
    "/farms/",
    "/farms/{farm_id}/weather",
    "/farms/{farm_id}/irrigation-events",
    "/farms/{farm_id}/baseline-irrigations",
    "/farms/{farm_id}/water-savings",
]


@pytest.mark.parametrize("path", LIST_PATHS)
def test_list_limit_over_100_rejected(client, farm, path):
    response = client.get(path.format(farm_id=farm.id), params={"limit": 101})
    assert response.status_code == 422


@pytest.mark.parametrize("path", LIST_PATHS)
def test_list_limit_100_accepted(client, farm, path):
    response = client.get(path.format(farm_id=farm.id), params={"limit": 100})
    assert response.status_code == 200


@pytest.mark.parametrize("path", LIST_PATHS)
def test_list_limit_zero_rejected(client, farm, path):
    response = client.get(path.format(farm_id=farm.id), params={"limit": 0})
    assert response.status_code == 422


@pytest.mark.parametrize("path", LIST_PATHS)
def test_list_negative_skip_rejected(client, farm, path):
    response = client.get(path.format(farm_id=farm.id), params={"skip": -1})
    assert response.status_code == 422


# ── field polygon ────────────────────────────────────────────────────────────


def test_create_farm_with_polygon_returns_wkt(client):
    response = client.post("/farms/", json={"name": "Poly Farm", "field_polygon": POLYGON_WKT})
    assert response.status_code == 200
    returned = response.json()["field_polygon"]
    assert shapely_wkt.loads(returned).equals(shapely_wkt.loads(POLYGON_WKT))


def test_update_farm_polygon(client, farm):
    response = client.put(f"/farms/{farm.id}", json={"field_polygon": POLYGON_WKT})
    assert response.status_code == 200
    returned = response.json()["field_polygon"]
    assert shapely_wkt.loads(returned).equals(shapely_wkt.loads(POLYGON_WKT))


# ── irrigation event routes ──────────────────────────────────────────────────


def test_log_irrigation_event(client, farm):
    response = client.post(
        f"/farms/{farm.id}/irrigation-events",
        json={"event_date": "2026-06-01", "gallons_applied": "1500.00"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["farm_id"] == farm.id
    assert data["source"] == "user_log"


def test_log_irrigation_event_unknown_farm(client):
    response = client.post(
        "/farms/9999/irrigation-events",
        json={"event_date": "2026-06-01", "gallons_applied": "1500.00"},
    )
    assert response.status_code == 404


def test_list_irrigation_events(client, farm):
    for day in ("2026-06-01", "2026-06-05"):
        client.post(
            f"/farms/{farm.id}/irrigation-events",
            json={"event_date": day, "gallons_applied": "100.00"},
        )
    response = client.get(f"/farms/{farm.id}/irrigation-events")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_list_irrigation_events_date_filter(client, farm):
    for day in ("2026-06-01", "2026-06-05", "2026-06-10"):
        client.post(
            f"/farms/{farm.id}/irrigation-events",
            json={"event_date": day, "gallons_applied": "100.00"},
        )
    response = client.get(
        f"/farms/{farm.id}/irrigation-events",
        params={"start_date": "2026-06-03", "end_date": "2026-06-08"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["event_date"] == "2026-06-05"


# ── baseline irrigation routes ───────────────────────────────────────────────


def test_create_baseline_irrigation(client, farm):
    response = client.post(
        f"/farms/{farm.id}/baseline-irrigations",
        json={"gallons_per_week_estimate": "5000.00"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["farm_id"] == farm.id
    assert data["gallons_per_week_estimate"] == "5000.00"
    assert data["created_at"] is not None


def test_create_baseline_irrigation_unknown_farm(client):
    response = client.post(
        "/farms/9999/baseline-irrigations",
        json={"gallons_per_week_estimate": "5000.00"},
    )
    assert response.status_code == 404


def test_create_baseline_irrigation_other_user_returns_404(client, db):
    other = User(email="other@example.com", hashed_password="dummy", name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)
    other_farm = crud.create_farm(db, FarmCreate(name="Other Farm"), user_id=other.id)
    response = client.post(
        f"/farms/{other_farm.id}/baseline-irrigations",
        json={"gallons_per_week_estimate": "5000.00"},
    )
    assert response.status_code == 404


def test_create_baseline_irrigation_unauthenticated(unauthed_client, farm):
    response = unauthed_client.post(
        f"/farms/{farm.id}/baseline-irrigations",
        json={"gallons_per_week_estimate": "5000.00"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize("bad_value", ["0", "-100.00"])
def test_create_baseline_irrigation_non_positive_rejected(client, farm, bad_value):
    response = client.post(
        f"/farms/{farm.id}/baseline-irrigations",
        json={"gallons_per_week_estimate": bad_value},
    )
    assert response.status_code == 422


def test_list_baseline_irrigations(client, farm):
    for value in ("4000.00", "6000.00"):
        client.post(
            f"/farms/{farm.id}/baseline-irrigations",
            json={"gallons_per_week_estimate": value},
        )
    response = client.get(f"/farms/{farm.id}/baseline-irrigations")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["results"]) == 2


def test_list_baseline_irrigations_unknown_farm(client):
    response = client.get("/farms/9999/baseline-irrigations")
    assert response.status_code == 404


# ── water savings routes ─────────────────────────────────────────────────────


def _add_water_savings(db, farm_id, start, end):
    row = WaterSavings(
        farm_id=farm_id,
        period_start=start,
        period_end=end,
        baseline_gallons=Decimal("1000.00"),
        actual_gallons=Decimal("800.00"),
        gallons_saved=Decimal("200.00"),
        kwh_saved=Decimal("5.00"),
        co2_kg_saved=Decimal("2.00"),
    )
    db.add(row)
    db.commit()
    return row


def test_list_water_savings(client, db, farm):
    _add_water_savings(db, farm.id, date(2026, 5, 1), date(2026, 5, 31))
    response = client.get(f"/farms/{farm.id}/water-savings")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["gallons_saved"] == "200.00"


def test_list_water_savings_date_filter(client, db, farm):
    _add_water_savings(db, farm.id, date(2026, 4, 1), date(2026, 4, 30))
    _add_water_savings(db, farm.id, date(2026, 5, 1), date(2026, 5, 31))
    response = client.get(
        f"/farms/{farm.id}/water-savings",
        params={"start_date": "2026-05-01", "end_date": "2026-05-31"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_water_savings_unknown_farm(client):
    response = client.get("/farms/9999/water-savings")
    assert response.status_code == 404

