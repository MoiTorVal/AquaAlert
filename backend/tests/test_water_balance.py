import pytest
from types import SimpleNamespace
from backend.services.water_balance import (
    _get_kc,
    _get_depletion_fraction,
    _compute_paw,
    _classify_severity,
    compute_water_balance,
)


# ── helpers ──────────────────────────────────────────────────────────────────


def make_farm(**kwargs):
    defaults = dict(
        field_capacity_pct=30,
        wilting_point_pct=15,
        root_depth_cm=60,
        crop_type="tomato",
        growth_stage="mid",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── _get_kc ──────────────────────────────────────────────────────────────────


def test_get_kc_known_crop_and_stage():
    assert _get_kc("tomato", "mid") == 1.15


def test_get_kc_unknown_crop_falls_back_to_default():
    assert _get_kc("banana", "mid") == 1.00  # default mid


def test_get_kc_none_crop_falls_back_to_default():
    assert _get_kc(None, "mid") == 1.00


def test_get_kc_invalid_stage_falls_back_to_mid():
    assert _get_kc("tomato", "flowering") == 1.15  # mid fallback


def test_get_kc_case_insensitive():
    assert _get_kc("TOMATO", "MID") == _get_kc("tomato", "mid")


# ── _get_depletion_fraction ──────────────────────────────────────────────────


def test_depletion_fraction_known_crop():
    assert _get_depletion_fraction("tomato") == 0.4


def test_depletion_fraction_unknown_crop():
    assert _get_depletion_fraction("banana") == 0.50  # default


def test_depletion_fraction_none():
    assert _get_depletion_fraction(None) == 0.50


# ── _compute_paw ─────────────────────────────────────────────────────────────


def test_compute_paw_normal():
    # (30 - 15) / 100 * 600mm = 90mm
    assert _compute_paw(30, 15, 600) == 90.0


def test_compute_paw_fc_equals_wp():
    # No available water if field capacity == wilting point
    assert _compute_paw(20, 20, 600) == 0.0


def test_compute_paw_zero_root_depth():
    assert _compute_paw(30, 15, 0) == 0.0


# ── _classify_severity ───────────────────────────────────────────────────────


def test_severity_high_when_depletion_exceeds_paw():
    assert _classify_severity(depletion_mm=100, raw_mm=45, paw_mm=90) == "high"


def test_severity_medium_when_depletion_exceeds_raw():
    assert _classify_severity(depletion_mm=50, raw_mm=45, paw_mm=90) == "medium"


def test_severity_low_when_depletion_near_raw():
    # raw * 0.75 = 33.75, so 35 is between 33.75 and 45
    assert _classify_severity(depletion_mm=35, raw_mm=45, paw_mm=90) == "low"


def test_severity_none_when_well_watered():
    assert _classify_severity(depletion_mm=10, raw_mm=45, paw_mm=90) == "None"


# ── compute_water_balance ────────────────────────────────────────────────────


def test_water_balance_with_soil_moisture():
    """Depletion calculated from soil moisture sensor reading"""
    farm = make_farm(field_capacity_pct=30, wilting_point_pct=15, root_depth_cm=60)
    sm = SimpleNamespace(soil_moisture_pct=24)  # 6% below FC
    # depletion = (30 - 24) / 100 * 600 = 36mm
    result = compute_water_balance(farm, weather_reading=None, soil_moisture_reading=sm)
    assert result.current_depletion_mm == 36.0


def test_water_balance_with_weather_readings():
    """Depletion calculated from ET0 and rainfall when no sensor"""
    farm = make_farm()
    readings = [
        SimpleNamespace(et0_mm=5.0, rainfall_mm=2.0),  # net = 5*1.15 - 2 = 3.75
        SimpleNamespace(et0_mm=5.0, rainfall_mm=0.0),  # net = 5.75
    ]
    result = compute_water_balance(farm, weather_reading=readings)
    assert result.current_depletion_mm == pytest.approx(9.5, abs=0.01)


def test_water_balance_no_readings_depletion_is_zero():
    """No sensor, no weather → depletion defaults to 0"""
    farm = make_farm()
    result = compute_water_balance(farm, weather_reading=None)
    assert result.current_depletion_mm == 0.0


def test_water_balance_forecast_gives_stress_days():
    """With ET0 forecast, stress_in_days should be calculated"""
    farm = make_farm()
    result = compute_water_balance(farm, weather_reading=None, et0_forecast_mm_per_day=5.0)
    assert result.stress_in_days is not None
    assert result.stress_in_days > 0


def test_water_balance_already_stressed_gives_zero_days():
    """If already past RAW threshold, stress_in_days = 0"""
    farm = make_farm(field_capacity_pct=30, wilting_point_pct=15, root_depth_cm=60)
    # Force high depletion via soil moisture near wilting point
    sm = SimpleNamespace(soil_moisture_pct=16)  # nearly depleted
    result = compute_water_balance(
        farm, weather_reading=None, soil_moisture_reading=sm, et0_forecast_mm_per_day=5.0
    )
    assert result.stress_in_days == 0


def test_water_balance_warning_true_when_stressed():
    farm = make_farm()
    sm = SimpleNamespace(soil_moisture_pct=16)
    result = compute_water_balance(farm, weather_reading=None, soil_moisture_reading=sm)
    assert result.warning is True


def test_water_balance_warning_false_when_healthy():
    farm = make_farm()
    sm = SimpleNamespace(soil_moisture_pct=30)  # at field capacity, no depletion
    result = compute_water_balance(farm, weather_reading=None, soil_moisture_reading=sm)
    assert result.warning is False
