import pytest
from types import SimpleNamespace
from backend.services.soil_moisture_model import estimate_soil_moisture


# ── fixtures / helpers ────────────────────────────────────────────────────────


def make_farm(**kwargs):
    defaults = dict(
        field_capacity_pct=30.0,
        wilting_point_pct=15.0,
        root_depth_cm=60.0,
        crop_type="tomato",
        growth_stage="mid",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_reading(et0_mm=5.0, rainfall_mm=0.0):
    return SimpleNamespace(et0_mm=et0_mm, rainfall_mm=rainfall_mm)


# ── estimate_soil_moisture ────────────────────────────────────────────────────


def test_no_readings_returns_field_capacity():
    """No weather readings → moisture stays at field capacity (the default initial)."""
    farm = make_farm()
    result = estimate_soil_moisture(farm, [])
    assert result == 30.0


def test_initial_moisture_used_when_provided():
    """Explicit initial_moisture_pct overrides field capacity."""
    farm = make_farm()
    result = estimate_soil_moisture(farm, [], initial_moisture_pct=22.0)
    assert result == 22.0


def test_et0_reduces_moisture():
    """ET0 consumption should lower soil moisture below field capacity."""
    farm = make_farm()
    # tomato mid: Kc=1.15, etc=5*1.15=5.75, delta=(5.75/600)*15=0.14375 → ~29.86
    result = estimate_soil_moisture(farm, [make_reading(et0_mm=5.0, rainfall_mm=0.0)])
    assert result < 30.0
    assert result == pytest.approx(29.86, abs=0.01)


def test_rainfall_increases_moisture():
    """Large rainfall should push moisture up to field capacity cap."""
    farm = make_farm()
    result = estimate_soil_moisture(
        farm,
        [make_reading(et0_mm=0.0, rainfall_mm=1000.0)],
        initial_moisture_pct=20.0,
    )
    assert result == 30.0  # capped at field capacity


def test_moisture_clamped_to_wilting_point():
    """Severe drought: moisture cannot drop below wilting point."""
    farm = make_farm()
    readings = [make_reading(et0_mm=50.0, rainfall_mm=0.0)] * 20
    result = estimate_soil_moisture(farm, readings)
    assert result == 15.0  # clamped to wilting point


def test_moisture_clamped_to_field_capacity():
    """Heavy rain on moist soil: moisture cannot exceed field capacity."""
    farm = make_farm()
    result = estimate_soil_moisture(
        farm,
        [make_reading(et0_mm=0.0, rainfall_mm=500.0)],
        initial_moisture_pct=28.0,
    )
    assert result == 30.0


def test_zero_et0_and_zero_rainfall_unchanged():
    """Zero ET and rainfall leaves moisture exactly as given."""
    farm = make_farm()
    result = estimate_soil_moisture(
        farm,
        [make_reading(et0_mm=0.0, rainfall_mm=0.0)],
        initial_moisture_pct=25.0,
    )
    assert result == 25.0


def test_multiple_readings_deplete_more_than_single():
    """Each additional high-ET reading should further lower moisture."""
    farm = make_farm()
    r = make_reading(et0_mm=2.0, rainfall_mm=0.0)
    result_single = estimate_soil_moisture(farm, [r])
    result_double = estimate_soil_moisture(farm, [r, r])
    assert result_double < result_single


def test_unknown_crop_uses_lower_default_kc():
    """Unknown crop defaults to Kc=1.0 (< tomato mid 1.15), so depletes less."""
    farm_tomato = make_farm(crop_type="tomato")
    farm_unknown = make_farm(crop_type="banana")
    r = make_reading(et0_mm=5.0, rainfall_mm=0.0)
    result_tomato = estimate_soil_moisture(farm_tomato, [r])
    result_unknown = estimate_soil_moisture(farm_unknown, [r])
    # tomato Kc=1.15 > default Kc=1.0 → tomato depletes more → lower moisture
    assert result_tomato < result_unknown


def test_none_et0_and_rainfall_treated_as_zero():
    """None values for et0_mm and rainfall_mm should default to 0."""
    farm = make_farm()
    result = estimate_soil_moisture(
        farm,
        [SimpleNamespace(et0_mm=None, rainfall_mm=None)],
        initial_moisture_pct=25.0,
    )
    assert result == 25.0


def test_result_is_rounded_to_two_decimal_places():
    """Output should always be rounded to 2 decimal places."""
    farm = make_farm()
    result = estimate_soil_moisture(farm, [make_reading(et0_mm=3.0)])
    assert result == round(result, 2)
