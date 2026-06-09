import pytest
from datetime import datetime, timezone, timedelta
from backend.models import User
from backend import crud
from backend.schemas import FarmCreate, WeatherReadingCreate


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
    deleted = crud.delete_farm(db, farm)
    assert deleted.id == farm.id
    assert crud.get_farm(db, farm.id) is None


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



# ── additional coverage ──────────────────────────────────────────────────────


def test_get_weather_reading_by_id(db, farm):
    created = crud.create_weather_reading(db, make_weather(farm.id))
    result = crud.get_weather_reading(db, created.id)
    assert result is not None
    assert result.id == created.id


def test_get_weather_reading_not_found(db):
    result = crud.get_weather_reading(db, 9999)
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



def test_update_farm(db, farm):
    from backend.schemas import FarmUpdate
    updated = crud.update_farm(db, farm, FarmUpdate(name="Updated Farm"))
    assert updated.name == "Updated Farm"
    assert updated.crop_type == "tomato"


def test_update_farm_only_changes_provided_fields(db, farm):
    from backend.schemas import FarmUpdate
    updated = crud.update_farm(db, farm, FarmUpdate(crop_type="corn"))
    assert updated.crop_type == "corn"
    assert updated.name == "Test Farm"


def test_get_farms_pagination(db, user):
    for i in range(5):
        crud.create_farm(db, FarmCreate(name=f"Farm {i}"), user_id=user.id)
    results = crud.get_farms(db, user_id=user.id, skip=2, limit=2)
    assert len(results) == 2


# ── field polygon ────────────────────────────────────────────────────────────


POLYGON_WKT = "POLYGON ((-120.5 36.5, -120.4 36.5, -120.4 36.6, -120.5 36.6, -120.5 36.5))"


def test_create_farm_with_polygon(db, user):
    from geoalchemy2.shape import to_shape
    from shapely import wkt as shapely_wkt

    result = crud.create_farm(
        db,
        FarmCreate(name="Poly Farm", field_polygon=POLYGON_WKT),
        user_id=user.id,
    )
    assert result.field_polygon is not None
    assert to_shape(result.field_polygon).equals(shapely_wkt.loads(POLYGON_WKT))


def test_update_farm_polygon(db, farm):
    from backend.schemas import FarmUpdate
    from geoalchemy2.shape import to_shape
    from shapely import wkt as shapely_wkt

    updated = crud.update_farm(db, farm, FarmUpdate(field_polygon=POLYGON_WKT))
    assert to_shape(updated.field_polygon).equals(shapely_wkt.loads(POLYGON_WKT))


def test_update_farm_without_polygon_leaves_it_unchanged(db, user):
    from backend.schemas import FarmUpdate

    farm = crud.create_farm(
        db,
        FarmCreate(name="Poly Farm", field_polygon=POLYGON_WKT),
        user_id=user.id,
    )
    updated = crud.update_farm(db, farm, FarmUpdate(name="Renamed"))
    assert updated.field_polygon is not None


# ── baseline irrigation CRUD ─────────────────────────────────────────────────


def test_create_baseline_irrigation(db, farm):
    from decimal import Decimal
    from backend.schemas import BaselineIrrigationCreate

    result = crud.create_baseline_irrigation(
        db, farm_id=farm.id,
        baseline=BaselineIrrigationCreate(gallons_per_week_estimate=Decimal("5000.00")),
    )
    assert result.id is not None
    assert result.farm_id == farm.id
    assert result.gallons_per_week_estimate == Decimal("5000.00")
    assert result.created_at is not None


def test_get_baseline_irrigations_newest_first(db, farm):
    from decimal import Decimal
    from backend.schemas import BaselineIrrigationCreate

    for value in ("4000.00", "6000.00"):
        crud.create_baseline_irrigation(
            db, farm_id=farm.id,
            baseline=BaselineIrrigationCreate(gallons_per_week_estimate=Decimal(value)),
        )
    results = crud.get_baseline_irrigations_by_farm(db, farm_id=farm.id)
    assert len(results) == 2
    assert results[0].created_at >= results[1].created_at


def test_count_baseline_irrigations_by_farm(db, farm):
    from decimal import Decimal
    from backend.schemas import BaselineIrrigationCreate

    crud.create_baseline_irrigation(
        db, farm_id=farm.id,
        baseline=BaselineIrrigationCreate(gallons_per_week_estimate=Decimal("5000.00")),
    )
    assert crud.count_baseline_irrigations_by_farm(db, farm_id=farm.id) == 1
