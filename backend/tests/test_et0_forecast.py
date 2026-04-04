import pytest
from backend.services.et0_forecast import _compute_ra, _compute_et0_day, forecast_et0


# ── _compute_ra ──────────────────────────────────────────────────────────────


def test_ra_equator_equinox():
    """Ra at equator on spring equinox should be ~36-38 MJ/m²/day"""
    ra = _compute_ra(latitude_deg=0.0, day_of_year=80)
    assert 36 < ra < 38


def test_ra_higher_latitude_less_in_winter():
    """Higher latitudes get less Ra in winter"""
    ra_equator = _compute_ra(latitude_deg=0.0, day_of_year=355)
    ra_north = _compute_ra(latitude_deg=50.0, day_of_year=355)
    assert ra_north < ra_equator


def test_ra_southern_hemisphere():
    """Southern hemisphere gets more Ra in December (their summer)"""
    ra_north = _compute_ra(latitude_deg=30.0, day_of_year=355)
    ra_south = _compute_ra(latitude_deg=-30.0, day_of_year=355)
    assert ra_south > ra_north


def test_ra_day1_vs_day365():
    """Day 1 and day 365 should be close to each other (both near winter solstice)"""
    ra_day1 = _compute_ra(latitude_deg=35.0, day_of_year=1)
    ra_day365 = _compute_ra(latitude_deg=35.0, day_of_year=365)
    assert abs(ra_day1 - ra_day365) < 1.0


def test_ra_always_positive():
    """Ra should always be positive for non-polar latitudes"""
    for lat in [-60, -30, 0, 30, 60]:
        for doy in [1, 80, 172, 265, 355]:
            ra = _compute_ra(latitude_deg=lat, day_of_year=doy)
            assert ra > 0, f"Ra was not positive at lat={lat}, doy={doy}"


def test_ra_polar_latitude_raises():
    """Latitude 90° causes math domain error (tan is undefined)"""
    with pytest.raises((ValueError, Exception)):
        _compute_ra(latitude_deg=90.0, day_of_year=355)


# ── _compute_et0_day ─────────────────────────────────────────────────────────


def test_et0_day_normal():
    """Hot summer day should produce a reasonable ET0"""
    et0 = _compute_et0_day(t_max_c=35, t_min_c=20, ra_mm=15.0)
    assert 4 < et0 < 12


def test_et0_day_equal_temps():
    """When t_max == t_min, sqrt(0) = 0, so ET0 must be 0"""
    et0 = _compute_et0_day(t_max_c=25, t_min_c=25, ra_mm=15.0)
    assert et0 == 0.0


def test_et0_day_inverted_temps_raises():
    """t_max < t_min is bad data — sqrt of negative should raise"""
    with pytest.raises(ValueError, match="t_max"):
        _compute_et0_day(t_max_c=15, t_min_c=25, ra_mm=15.0)


def test_et0_day_cold_temperatures():
    """Cold day should produce low but non-negative ET0"""
    et0 = _compute_et0_day(t_max_c=5, t_min_c=-5, ra_mm=5.0)
    assert 0 <= et0 < 3


def test_et0_day_scales_with_radiation():
    """Higher Ra should produce higher ET0 (all else equal)"""
    et0_low = _compute_et0_day(t_max_c=30, t_min_c=15, ra_mm=5.0)
    et0_high = _compute_et0_day(t_max_c=30, t_min_c=15, ra_mm=15.0)
    assert et0_high > et0_low


# ── forecast_et0 ─────────────────────────────────────────────────────────────


def test_forecast_et0_empty_list():
    result = forecast_et0([], latitude_deg=35.0)
    assert result == 0.0


def test_forecast_et0_known_values():
    """Plug in known values and check reasonable range"""
    days = [{"date": "2026-07-01", "t_max_c": 35, "t_min_c": 20}]
    result = forecast_et0(days, latitude_deg=35.0)
    assert 4 < result < 10


def test_forecast_et0_multi_day_average():
    """Result should be the average across all days, not the sum"""
    day = {"date": "2026-07-01", "t_max_c": 35, "t_min_c": 20}
    single = forecast_et0([day], latitude_deg=35.0)
    multi = forecast_et0([day, day, day], latitude_deg=35.0)
    assert abs(single - multi) < 0.001  # same day repeated → same average


def test_forecast_et0_bad_date_raises():
    """A malformed date string should raise ValueError"""
    days = [{"date": "not-a-date", "t_max_c": 35, "t_min_c": 20}]
    with pytest.raises(ValueError):
        forecast_et0(days, latitude_deg=35.0)
