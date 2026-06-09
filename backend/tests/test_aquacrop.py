from datetime import date, timedelta
from decimal import Decimal

import pytest

from backend import crud
from backend.enums import SoilTexture, StressSeverity
from backend.schemas import AquaCropOutputBase, ETReadingCreate, FarmCreate
from backend.services import aquacrop_runner
from backend.services.aquacrop_runner import (
    AquaCropInputError,
    classify_severity,
    compute_and_cache_water_stress,
    map_crop_type,
    map_soil_texture,
    project_days_to_stress,
    run_simulation,
)

START = date(2026, 5, 1)
CONSTANT_ET = [(START + timedelta(days=i), 5.0) for i in range(30)]


# ── mappings ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("crop_type,expected", [
    ("corn", "Maize"),
    ("Corn", "Maize"),
    ("maize", "Maize"),
    ("wheat", "Wheat"),
    ("tomato", "Tomato"),
    ("rice", "PaddyRice"),
])
def test_map_crop_type(crop_type, expected):
    assert map_crop_type(crop_type) == expected


def test_map_crop_type_unknown_raises():
    with pytest.raises(AquaCropInputError, match="Unsupported crop type"):
        map_crop_type("dragonfruit")


def test_map_crop_type_none_raises():
    with pytest.raises(AquaCropInputError, match="no crop_type"):
        map_crop_type(None)


@pytest.mark.parametrize("texture", list(SoilTexture))
def test_every_soil_texture_maps_to_valid_aquacrop_soil(texture):
    from aquacrop import Soil

    Soil(map_soil_texture(texture))  # raises if the name is invalid


def test_map_soil_texture_none_raises():
    with pytest.raises(AquaCropInputError, match="no soil_type"):
        map_soil_texture(None)


# ── severity + projection (pure helpers) ─────────────────────────────────────


def test_classify_severity_green_below_warning():
    assert classify_severity(10.0, 100.0) == StressSeverity.GREEN


def test_classify_severity_yellow_at_warning_fraction():
    assert classify_severity(80.0, 100.0) == StressSeverity.YELLOW


def test_classify_severity_red_at_threshold():
    assert classify_severity(100.0, 100.0) == StressSeverity.RED


def test_project_days_to_stress_linear_rate():
    # depletion rising 2 mm/day, 10 mm of headroom left -> 5 days
    series = [40.0, 42.0, 44.0, 46.0, 48.0, 50.0]
    assert project_days_to_stress(series, 60.0) == 5


def test_project_days_to_stress_already_stressed_returns_zero():
    assert project_days_to_stress([70.0], 60.0) == 0


def test_project_days_to_stress_flat_returns_none():
    assert project_days_to_stress([40.0, 40.0, 40.0], 60.0) is None


def test_project_days_to_stress_recovering_returns_none():
    assert project_days_to_stress([50.0, 45.0, 40.0], 60.0) is None


def test_project_days_to_stress_single_point_returns_none():
    assert project_days_to_stress([40.0], 60.0) is None


# ── run_simulation input validation ──────────────────────────────────────────


def test_run_simulation_requires_planting_date():
    with pytest.raises(AquaCropInputError, match="planting_date"):
        run_simulation(CONSTANT_ET, "corn", SoilTexture.SandyLoam, None)


def test_run_simulation_requires_et_series():
    with pytest.raises(AquaCropInputError, match="empty"):
        run_simulation([], "corn", SoilTexture.SandyLoam, START)


def test_run_simulation_rejects_planting_before_series():
    with pytest.raises(AquaCropInputError, match="on or before planting_date"):
        run_simulation(CONSTANT_ET, "corn", SoilTexture.SandyLoam, START - timedelta(days=5))


def test_run_simulation_rejects_planting_after_series():
    with pytest.raises(AquaCropInputError, match="after the ET series end"):
        run_simulation(CONSTANT_ET, "corn", SoilTexture.SandyLoam, START + timedelta(days=60))


# ── golden fixtures: corn + sandy loam + 30d ET ──────────────────────────────
# Values recorded from aquacrop==3.0.12 on 2026-06-09; loose tolerances so
# patch-level library updates don't break the suite.

GOLDEN_CONSTANT = {
    "depletion_mm": 33.42,
    "paw_mm": 76.98,
    "raw_threshold_mm": 76.18,
    "root_zone_moisture_pct": 69.72,
    "severity": StressSeverity.GREEN,
    "days_to_stress": 41,
}

GOLDEN_VARIED = {
    "depletion_mm": 32.26,
    "severity": StressSeverity.GREEN,
}


def test_golden_corn_sandyloam_constant_et():
    result = run_simulation(CONSTANT_ET, "corn", SoilTexture.SandyLoam, START)
    assert result.as_of_date == date(2026, 5, 30)
    assert float(result.depletion_mm) == pytest.approx(GOLDEN_CONSTANT["depletion_mm"], abs=2.0)
    assert float(result.paw_mm) == pytest.approx(GOLDEN_CONSTANT["paw_mm"], abs=2.0)
    assert float(result.raw_threshold_mm) == pytest.approx(GOLDEN_CONSTANT["raw_threshold_mm"], abs=2.0)
    assert float(result.root_zone_moisture_pct) == pytest.approx(GOLDEN_CONSTANT["root_zone_moisture_pct"], abs=2.0)
    assert result.severity == GOLDEN_CONSTANT["severity"]
    assert result.days_to_stress == pytest.approx(GOLDEN_CONSTANT["days_to_stress"], abs=3)


def test_golden_corn_sandyloam_varied_et():
    varied = [(START + timedelta(days=i), 3.0 + 2.5 * (i % 7) / 6) for i in range(30)]
    result = run_simulation(varied, "corn", SoilTexture.SandyLoam, START)
    assert float(result.depletion_mm) == pytest.approx(GOLDEN_VARIED["depletion_mm"], abs=2.0)
    assert result.severity == GOLDEN_VARIED["severity"]


def test_run_simulation_is_deterministic():
    first = run_simulation(CONSTANT_ET, "corn", SoilTexture.SandyLoam, START)
    second = run_simulation(CONSTANT_ET, "corn", SoilTexture.SandyLoam, START)
    assert first == second


# ── DB edge: compute_and_cache_water_stress ──────────────────────────────────


@pytest.fixture
def sim_farm(db, user):
    return crud.create_farm(
        db,
        FarmCreate(
            name="Sim Farm",
            crop_type="corn",
            soil_type=SoilTexture.SandyLoam,
            planting_date=START,
        ),
        user_id=user.id,
    )


def _seed_et(db, farm_id, days=30):
    crud.create_et_readings(db, [
        ETReadingCreate(
            farm_id=farm_id,
            reading_date=START + timedelta(days=i),
            et_mm=5.0,
            source="openet:Ensemble",
        )
        for i in range(days)
    ])


def test_compute_and_cache_creates_output(db, sim_farm):
    _seed_et(db, sim_farm.id)
    output = compute_and_cache_water_stress(db, sim_farm, as_of_date=date(2026, 5, 30))
    assert output.id is not None
    assert output.farm_id == sim_farm.id
    assert output.as_of_date == date(2026, 5, 30)
    assert output.severity is not None


def test_compute_and_cache_upserts_on_rerun(db, sim_farm):
    _seed_et(db, sim_farm.id)
    first = compute_and_cache_water_stress(db, sim_farm, as_of_date=date(2026, 5, 30))
    second = compute_and_cache_water_stress(db, sim_farm, as_of_date=date(2026, 5, 30))
    assert second.id == first.id
    count = (
        db.query(crud.models.AquaCropOutput)
        .filter_by(farm_id=sim_farm.id, as_of_date=date(2026, 5, 30))
        .count()
    )
    assert count == 1


def test_compute_and_cache_missing_et_raises(db, sim_farm):
    with pytest.raises(AquaCropInputError):
        compute_and_cache_water_stress(db, sim_farm, as_of_date=date(2026, 5, 30))


# ── GET /farms/{id}/water-stress ─────────────────────────────────────────────


def _insert_output(db, farm_id, as_of, severity=StressSeverity.GREEN):
    return crud.upsert_aquacrop_output(db, farm_id, AquaCropOutputBase(
        as_of_date=as_of,
        depletion_mm=Decimal("30.00"),
        root_zone_moisture_pct=Decimal("70.00"),
        severity=severity,
        days_to_stress=12,
        paw_mm=Decimal("80.00"),
        raw_threshold_mm=Decimal("76.00"),
    ))


def test_water_stress_returns_latest(client, db, farm):
    _insert_output(db, farm.id, date(2026, 5, 28), StressSeverity.GREEN)
    _insert_output(db, farm.id, date(2026, 5, 30), StressSeverity.YELLOW)
    response = client.get(f"/farms/{farm.id}/water-stress")
    assert response.status_code == 200
    body = response.json()
    assert body["as_of_date"] == "2026-05-30"
    assert body["severity"] == "yellow"
    assert body["days_to_stress"] == 12


def test_water_stress_no_data_returns_404(client, farm):
    response = client.get(f"/farms/{farm.id}/water-stress")
    assert response.status_code == 404


def test_water_stress_unknown_farm(client):
    response = client.get("/farms/9999/water-stress")
    assert response.status_code == 404


def test_water_stress_other_user_returns_404(client, db):
    from backend.models import User

    other = User(email="other@example.com", hashed_password="dummy", name="Other")
    db.add(other)
    db.commit()
    db.refresh(other)
    other_farm = crud.create_farm(db, FarmCreate(name="Other Farm"), user_id=other.id)
    _insert_output(db, other_farm.id, date(2026, 5, 30))
    response = client.get(f"/farms/{other_farm.id}/water-stress")
    assert response.status_code == 404


def test_water_stress_unauthenticated(unauthed_client, farm):
    response = unauthed_client.get(f"/farms/{farm.id}/water-stress")
    assert response.status_code == 401
