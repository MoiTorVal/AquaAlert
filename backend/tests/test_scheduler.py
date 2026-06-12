import asyncio
from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import SecretStr

from backend import crud, models
from backend.config import settings
from backend.enums import JobStatus, Locale, SoilTexture, StressSeverity
from backend.schemas import AquaCropOutputBase, BaselineIrrigationCreate, ETReadingCreate, FarmCreate, IrrigationEventCreate
from backend.services import cimis_client, openet_client, rainfall_client, savings_calculator, sentinel_client, sms_service
from backend.services.aquacrop_runner import CROP_TYPE_TO_AQUACROP
from backend.services.cimis_client import CimisUnavailableError
from backend.services.openet_client import ET_SOURCE, OpenETRateLimitError, OpenETUnavailableError
from backend.services.rainfall_client import RainfallUnavailableError
from backend.services.sentinel_client import SentinelUnavailableError
from backend.services.sms_service import SmsError
from backend.services.scheduler import (
    ET_SIM_JOB_NAME,
    KC_MID,
    PROVISIONAL_ET_SOURCE,
    RAIN_REFRESH_DAYS,
    SATELLITE_SCANS_JOB_NAME,
    SAVINGS_JOB_NAME,
    is_et_stale,
    run_et_sim_job,
    run_satellite_scans_job,
    run_savings_job,
)

START = date(2026, 5, 1)
TODAY = date(2026, 6, 9)  # a Tuesday; last completed week = Jun 1 - Jun 7
FIELD_WKT = "POLYGON((-120.1 36.9, -120.1 36.91, -120.09 36.91, -120.09 36.9, -120.1 36.9))"


@pytest.fixture(autouse=True)
def no_rain(monkeypatch):
    """Stub Open-Meteo for every scheduler test (no network); records calls.

    Individual tests override with rain data where it matters.
    """
    calls = []

    async def fake_fetch(lat, lng, start_date, end_date, today=None, transport=None):
        calls.append((start_date, end_date))
        return []

    monkeypatch.setattr(rainfall_client, "fetch_daily_precip", fake_fetch)
    return calls


@pytest.fixture(autouse=True)
def fake_satellite(monkeypatch):
    calls = []

    def fake_fetch(polygon, max_cloud_pct=15, lookback_days=14):
        calls.append((max_cloud_pct, lookback_days))
        return {
            "scan_date": TODAY,
            "cloud_cover_pct": 4.2,
            "mean_ndvi": 0.61,
            "max_ndvi": 0.78,
            "min_ndvi": 0.41,
            "ndvi_grid": [[0.5, 0.6], [None, 0.7]],
            "ndvi_grid_bounds": [[36.9, -120.1], [36.91, -120.09]],
        }

    monkeypatch.setattr(sentinel_client, "fetch_latest_ndvi", fake_fetch)
    return calls


# ── savings_calculator (pure) ────────────────────────────────────────────────


def test_gallons_to_kwh_known_value():
    # 10,000 gal lifted 100 ft at 55% plant efficiency
    assert savings_calculator.gallons_to_kwh(Decimal("10000"), Decimal("100")) == Decimal("5.71")


def test_gallons_to_kwh_preserves_negative_sign():
    assert savings_calculator.gallons_to_kwh(Decimal("-10000"), Decimal("100")) == Decimal("-5.71")


def test_gallons_to_kwh_no_lift_returns_zero():
    assert savings_calculator.gallons_to_kwh(Decimal("10000"), None) == Decimal("0.00")


def test_kwh_to_co2():
    assert savings_calculator.kwh_to_co2_kg(Decimal("100")) == Decimal("22.60")


def test_week_bounds_midweek():
    assert savings_calculator.week_bounds(date(2026, 6, 10)) == (date(2026, 6, 8), date(2026, 6, 14))


def test_week_bounds_monday_and_sunday():
    assert savings_calculator.week_bounds(date(2026, 6, 8)) == (date(2026, 6, 8), date(2026, 6, 14))
    assert savings_calculator.week_bounds(date(2026, 6, 14)) == (date(2026, 6, 8), date(2026, 6, 14))


def test_last_completed_week():
    assert savings_calculator.last_completed_week(TODAY) == (date(2026, 6, 1), date(2026, 6, 7))
    # Monday: the week that just ended yesterday
    assert savings_calculator.last_completed_week(date(2026, 6, 8)) == (date(2026, 6, 1), date(2026, 6, 7))


# ── stale guard ──────────────────────────────────────────────────────────────


def test_is_et_stale_none():
    assert is_et_stale(None, TODAY) is True


def test_is_et_stale_old_reading():
    assert is_et_stale(TODAY - timedelta(days=8), TODAY) is True


def test_is_et_stale_fresh_reading():
    assert is_et_stale(TODAY - timedelta(days=3), TODAY) is False
    assert is_et_stale(TODAY - timedelta(days=7), TODAY) is False


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def sim_farm(db, user):
    return crud.create_farm(
        db,
        FarmCreate(
            name="Scheduler Farm",
            crop_type="corn",
            soil_type=SoilTexture.SandyLoam,
            planting_date=START,
            field_polygon=FIELD_WKT,
            pump_lift_ft=100,
        ),
        user_id=user.id,
    )


@pytest.fixture
def fake_et(monkeypatch):
    """Replace the OpenET fetch with a deterministic local series; records calls."""
    calls = []

    async def fake_fetch(geometry, start_date, end_date, transport=None):
        calls.append((start_date, end_date))
        days = (end_date - start_date).days + 1
        # value varies by date so trim_gapfill_tail leaves the series alone
        return [
            {"reading_date": start_date + timedelta(days=i), "et_mm": 3.0 + ((start_date.toordinal() + i) % 5) * 0.5}
            for i in range(days)
        ]

    monkeypatch.setattr(openet_client, "fetch_daily_et", fake_fetch)
    return calls


# ── get_active_farms ─────────────────────────────────────────────────────────


def test_get_active_farms_filters(db, user):
    active = crud.create_farm(db, FarmCreate(name="A", planting_date=START), user_id=user.id)
    crud.create_farm(db, FarmCreate(name="Unplanted"), user_id=user.id)
    crud.create_farm(db, FarmCreate(name="Harvested", planting_date=START, harvest_date=TODAY - timedelta(days=1)), user_id=user.id)
    in_season = crud.create_farm(db, FarmCreate(name="InSeason", planting_date=START, harvest_date=TODAY + timedelta(days=30)), user_id=user.id)
    crud.create_farm(db, FarmCreate(name="Future", planting_date=TODAY + timedelta(days=5)), user_id=user.id)

    ids = {f.id for f in crud.get_active_farms(db, TODAY)}
    assert ids == {active.id, in_season.id}


# ── ET + sim job ─────────────────────────────────────────────────────────────


def test_et_sim_job_processes_farm(db, sim_farm, fake_et):
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.job_name == ET_SIM_JOB_NAME
    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_processed == 1
    assert job_run.finished_at is not None
    readings = crud.get_et_readings_by_farm(db, sim_farm.id)
    assert readings[0].reading_date == START
    assert readings[-1].reading_date == TODAY
    output = crud.get_latest_aquacrop_output(db, sim_farm.id)
    assert output is not None
    assert output.as_of_date == TODAY
    assert fake_et == [(START, TODAY)]


def test_et_sim_job_incremental_fetch(db, sim_farm, fake_et):
    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    asyncio.run(run_et_sim_job(db=db, today=TODAY + timedelta(days=1)))

    # second run only asks for the missing day — quota-frugal
    assert fake_et == [(START, TODAY), (TODAY + timedelta(days=1), TODAY + timedelta(days=1))]
    readings = crud.get_et_readings_by_farm(db, sim_farm.id)
    assert len(readings) == len({r.reading_date for r in readings})  # no duplicates


def test_et_sim_job_skips_unconfigured_farm(db, user, fake_et):
    crud.create_farm(db, FarmCreate(name="No polygon", crop_type="corn", soil_type=SoilTexture.SandyLoam, planting_date=START), user_id=user.id)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_skipped == 1
    assert "missing polygon/crop/soil" in job_run.detail
    assert fake_et == []


def test_et_sim_job_rate_limit_aborts(db, sim_farm, monkeypatch):
    async def quota_dead(*args, **kwargs):
        raise OpenETRateLimitError("quota", status_code=429)

    monkeypatch.setattr(openet_client, "fetch_daily_et", quota_dead)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert job_run.status == JobStatus.FAILED
    assert "quota exhausted" in job_run.detail


def test_et_sim_job_fetch_failure_continues(db, sim_farm, monkeypatch):
    async def unavailable(*args, **kwargs):
        raise OpenETUnavailableError("503")

    monkeypatch.setattr(openet_client, "fetch_daily_et", unavailable)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert job_run.status == JobStatus.FAILED
    assert job_run.farms_failed == 1
    assert "ET fetch failed" in job_run.detail


def test_et_sim_job_flags_stale_et(db, sim_farm, monkeypatch):
    stale_latest = TODAY - timedelta(days=10)
    crud.create_et_readings(db, [
        ETReadingCreate(farm_id=sim_farm.id, reading_date=START + timedelta(days=i), et_mm=5.0, source=ET_SOURCE)
        for i in range((stale_latest - START).days + 1)
    ])

    async def nothing_new(*args, **kwargs):
        return []

    monkeypatch.setattr(openet_client, "fetch_daily_et", nothing_new)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert job_run.status == JobStatus.SUCCESS  # sim still runs on old data
    assert "stale ET" in job_run.detail
    output = crud.get_latest_aquacrop_output(db, sim_farm.id)
    assert output.as_of_date == stale_latest


# ── CIMIS gap-fill ───────────────────────────────────────────────────────────


OPENET_LAG_DAYS = 6


@pytest.fixture
def lagged_et(monkeypatch):
    """OpenET fake with a realistic data lag: nothing newer than TODAY - 6."""
    calls = []

    async def fake_fetch(geometry, start_date, end_date, transport=None):
        calls.append((start_date, end_date))
        end = min(end_date, TODAY - timedelta(days=OPENET_LAG_DAYS))
        if start_date > end:
            return []
        days = (end - start_date).days + 1
        return [
            {"reading_date": start_date + timedelta(days=i), "et_mm": 3.0 + ((start_date.toordinal() + i) % 5) * 0.5}
            for i in range(days)
        ]

    monkeypatch.setattr(openet_client, "fetch_daily_et", fake_fetch)
    return calls


@pytest.fixture
def fake_cimis(monkeypatch):
    """Enable gap-fill and replace the CIMIS fetch with a flat 4.0 mm ETo series."""
    calls = []

    async def fake_fetch(lat, lng, start_date, end_date, transport=None):
        calls.append((lat, lng, start_date, end_date))
        days = (end_date - start_date).days + 1
        return [{"reading_date": start_date + timedelta(days=i), "eto_mm": 4.0} for i in range(days)]

    monkeypatch.setattr(settings, "cimis_app_key", SecretStr("test-cimis-key"))
    monkeypatch.setattr(cimis_client, "fetch_daily_eto", fake_fetch)
    return calls


def test_kc_table_covers_all_supported_crops():
    assert set(KC_MID) == set(CROP_TYPE_TO_AQUACROP)


def test_gapfill_bridges_openet_lag(db, sim_farm, lagged_et, fake_cimis):
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.status == JobStatus.SUCCESS
    # CIMIS asked exactly for the lag window, at the field centroid
    (lat, lng, gap_start, gap_end) = fake_cimis[0]
    assert (gap_start, gap_end) == (TODAY - timedelta(days=OPENET_LAG_DAYS - 1), TODAY - timedelta(days=1))
    assert lat == pytest.approx(36.905, abs=1e-3)
    assert lng == pytest.approx(-120.095, abs=1e-3)

    readings = {r.reading_date: r for r in crud.get_et_readings_by_farm(db, sim_farm.id)}
    assert max(readings) == TODAY - timedelta(days=1)
    provisional = readings[TODAY - timedelta(days=1)]
    assert provisional.source == PROVISIONAL_ET_SOURCE
    assert float(provisional.et_mm) == pytest.approx(4.0 * KC_MID["corn"])
    assert readings[TODAY - timedelta(days=OPENET_LAG_DAYS)].source == ET_SOURCE

    # sim consumed the provisional days — "as of yesterday (estimated)"
    output = crud.get_latest_aquacrop_output(db, sim_farm.id)
    assert output.as_of_date == TODAY - timedelta(days=1)


def test_openet_actuals_replace_provisional_rows(db, sim_farm, lagged_et, fake_cimis, monkeypatch):
    asyncio.run(run_et_sim_job(db=db, today=TODAY))  # first run: lagged → provisional tail

    calls = []

    async def caught_up(geometry, start_date, end_date, transport=None):
        calls.append((start_date, end_date))
        days = (end_date - start_date).days + 1
        return [
            {"reading_date": start_date + timedelta(days=i), "et_mm": 3.0 + ((start_date.toordinal() + i) % 5) * 0.5}
            for i in range(days)
        ]

    monkeypatch.setattr(openet_client, "fetch_daily_et", caught_up)
    asyncio.run(run_et_sim_job(db=db, today=TODAY))

    # refetch starts after the last ACTUAL, re-requesting provisional dates
    assert calls == [(TODAY - timedelta(days=OPENET_LAG_DAYS - 1), TODAY)]
    readings = crud.get_et_readings_by_farm(db, sim_farm.id)
    assert {r.source for r in readings} == {ET_SOURCE}  # no provisional rows left
    assert max(r.reading_date for r in readings) == TODAY


def test_gapfill_skipped_without_cimis_key(db, sim_farm, lagged_et, monkeypatch):
    monkeypatch.setattr(settings, "cimis_app_key", None)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.status == JobStatus.SUCCESS
    readings = crud.get_et_readings_by_farm(db, sim_farm.id)
    assert {r.source for r in readings} == {ET_SOURCE}
    assert max(r.reading_date for r in readings) == TODAY - timedelta(days=OPENET_LAG_DAYS)


def test_gapfill_failure_does_not_fail_farm(db, sim_farm, lagged_et, monkeypatch):
    monkeypatch.setattr(settings, "cimis_app_key", SecretStr("test-cimis-key"))

    async def cimis_down(*args, **kwargs):
        raise CimisUnavailableError("503")

    monkeypatch.setattr(cimis_client, "fetch_daily_eto", cimis_down)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.status == JobStatus.SUCCESS  # best-effort: sim ran on actuals
    assert job_run.farms_processed == 1
    assert "CIMIS gap-fill failed" in job_run.detail
    output = crud.get_latest_aquacrop_output(db, sim_farm.id)
    assert output.as_of_date == TODAY - timedelta(days=OPENET_LAG_DAYS)


def test_gapfill_handles_unpublished_cimis_days(db, sim_farm, lagged_et, monkeypatch):
    monkeypatch.setattr(settings, "cimis_app_key", SecretStr("test-cimis-key"))

    async def nothing_published(*args, **kwargs):
        return []

    monkeypatch.setattr(cimis_client, "fetch_daily_eto", nothing_published)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.status == JobStatus.SUCCESS
    readings = crud.get_et_readings_by_farm(db, sim_farm.id)
    assert {r.source for r in readings} == {ET_SOURCE}


def test_gapfill_flags_provisional_only_farms(db, sim_farm, fake_cimis, monkeypatch):
    """OpenET outage must not hide behind fresh provisional rows."""
    stale_latest = TODAY - timedelta(days=10)
    crud.create_et_readings(db, [
        ETReadingCreate(farm_id=sim_farm.id, reading_date=START + timedelta(days=i), et_mm=5.0, source=ET_SOURCE)
        for i in range((stale_latest - START).days + 1)
    ])

    async def nothing_new(*args, **kwargs):
        return []

    monkeypatch.setattr(openet_client, "fetch_daily_et", nothing_new)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.status == JobStatus.SUCCESS
    assert "running on provisional ET" in job_run.detail
    assert "stale ET" not in job_run.detail  # provisional rows keep the series fresh
    output = crud.get_latest_aquacrop_output(db, sim_farm.id)
    assert output.as_of_date == TODAY - timedelta(days=1)


# ── Open-Meteo rainfall pull ─────────────────────────────────────────────────


def test_rainfall_pull_caches_rain_and_feeds_sim(db, sim_farm, fake_et, monkeypatch):
    rain_day = TODAY - timedelta(days=3)

    async def rainy(lat, lng, start_date, end_date, today=None, transport=None):
        return [{"reading_date": rain_day, "precip_mm": 12.5}]

    monkeypatch.setattr(rainfall_client, "fetch_daily_precip", rainy)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.status == JobStatus.SUCCESS
    assert crud.get_rainfall_series(db, sim_farm.id, START, TODAY) == [(rain_day, 12.5)]
    assert crud.get_latest_aquacrop_output(db, sim_farm.id) is not None


def test_rainfall_pull_backfills_then_refreshes_trailing_window(db, sim_farm, fake_et, no_rain):
    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    # first run backfills the whole season up to yesterday
    assert no_rain[0] == (START, TODAY - timedelta(days=1))

    crud.upsert_rainfall_readings(
        db, sim_farm.id, [{"reading_date": TODAY - timedelta(days=1), "precip_mm": 0.0}]
    )
    asyncio.run(run_et_sim_job(db=db, today=TODAY + timedelta(days=1)))
    # later runs re-pull only the trailing refresh window (revisable days)
    assert no_rain[1] == (
        TODAY + timedelta(days=1) - timedelta(days=RAIN_REFRESH_DAYS),
        TODAY,
    )


def test_rainfall_refresh_updates_revised_values(db, sim_farm):
    day = TODAY - timedelta(days=2)
    crud.upsert_rainfall_readings(db, sim_farm.id, [{"reading_date": day, "precip_mm": 1.0}])
    crud.upsert_rainfall_readings(db, sim_farm.id, [{"reading_date": day, "precip_mm": 4.0}])
    assert crud.get_rainfall_series(db, sim_farm.id, START, TODAY) == [(day, 4.0)]


def test_rainfall_failure_does_not_fail_farm(db, sim_farm, fake_et, monkeypatch):
    async def meteo_down(*args, **kwargs):
        raise RainfallUnavailableError("503")

    monkeypatch.setattr(rainfall_client, "fetch_daily_precip", meteo_down)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_processed == 1
    assert "rainfall fetch failed" in job_run.detail
    assert crud.get_latest_aquacrop_output(db, sim_farm.id) is not None


def test_water_stress_reports_latest_actual_date(client, db, farm):
    actual = date.today() - timedelta(days=6)
    estimated = date.today() - timedelta(days=1)
    _cached_output(db, farm.id, estimated)
    crud.create_et_readings(db, [
        ETReadingCreate(farm_id=farm.id, reading_date=actual, et_mm=5.0, source=ET_SOURCE),
        ETReadingCreate(farm_id=farm.id, reading_date=estimated, et_mm=4.8, source=PROVISIONAL_ET_SOURCE),
    ])

    body = client.get(f"/farms/{farm.id}/water-stress").json()
    assert body["et_latest_date"] == estimated.isoformat()
    assert body["et_latest_actual_date"] == actual.isoformat()
    assert body["et_is_stale"] is False


# ── SMS alert dispatch ───────────────────────────────────────────────────────


@pytest.fixture
def twilio_settings(monkeypatch):
    monkeypatch.setattr(settings, "twilio_account_sid", "ACtest")
    monkeypatch.setattr(settings, "twilio_auth_token", SecretStr("token"))
    monkeypatch.setattr(settings, "twilio_from_number", "+15550006666")


@pytest.fixture
def sms_farmer(db, user):
    user.phone_number = "+15551112222"
    user.sms_alerts_enabled = True
    db.commit()
    return user


@pytest.fixture
def sent_sms(monkeypatch):
    calls = []

    async def fake_send(to, body, transport=None):
        calls.append((to, body))
        return f"SM{len(calls)}"

    monkeypatch.setattr(sms_service, "send_sms", fake_send)
    return calls


def _force_sim_severity(monkeypatch, severity, days_to_stress=3):
    """Pin the sim output: severity escalation logic is what's under test,
    not AquaCrop."""
    from backend.services import scheduler as scheduler_module

    def fake(db, farm, as_of_date):
        return crud.upsert_aquacrop_output(db, farm.id, AquaCropOutputBase(
            as_of_date=as_of_date,
            depletion_mm=Decimal("50.00"),
            root_zone_moisture_pct=Decimal("50.00"),
            severity=severity,
            days_to_stress=days_to_stress,
            paw_mm=Decimal("50.00"),
            raw_threshold_mm=Decimal("60.00"),
        ))

    monkeypatch.setattr(scheduler_module, "compute_and_cache_water_stress", fake)


def _seed_severity(db, farm_id, severity, as_of):
    crud.upsert_aquacrop_output(db, farm_id, AquaCropOutputBase(
        as_of_date=as_of, depletion_mm=Decimal("40.00"), root_zone_moisture_pct=Decimal("60.00"),
        severity=severity, days_to_stress=5, paw_mm=Decimal("60.00"), raw_threshold_mm=Decimal("60.00"),
    ))


def test_alert_sent_on_escalation(db, sim_farm, fake_et, twilio_settings, sms_farmer, sent_sms, monkeypatch):
    _seed_severity(db, sim_farm.id, StressSeverity.GREEN, TODAY - timedelta(days=1))
    _force_sim_severity(monkeypatch, StressSeverity.RED, days_to_stress=2)

    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert job_run.status == JobStatus.SUCCESS
    (to, body), = sent_sms
    assert to == sms_farmer.phone_number
    assert "RED" in body and sim_farm.name in body
    alert = crud.get_alert(db, sim_farm.id, TODAY, StressSeverity.RED)
    assert alert is not None
    assert alert.provider_message_sid == "SM1"
    assert alert.days_to_stress == 2
    assert "alerts sent: 1" in job_run.detail


def test_alert_spanish_locale(db, sim_farm, fake_et, twilio_settings, sms_farmer, sent_sms, monkeypatch):
    sms_farmer.locale = Locale.ES
    db.commit()
    _force_sim_severity(monkeypatch, StressSeverity.RED)

    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    (_, body), = sent_sms
    assert "ROJO" in body


def test_no_alert_when_severity_unchanged(db, sim_farm, fake_et, twilio_settings, sms_farmer, sent_sms, monkeypatch):
    _seed_severity(db, sim_farm.id, StressSeverity.RED, TODAY - timedelta(days=1))
    _force_sim_severity(monkeypatch, StressSeverity.RED)

    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert sent_sms == []


def test_no_alert_on_deescalation(db, sim_farm, fake_et, twilio_settings, sms_farmer, sent_sms, monkeypatch):
    _seed_severity(db, sim_farm.id, StressSeverity.RED, TODAY - timedelta(days=1))
    _force_sim_severity(monkeypatch, StressSeverity.YELLOW)

    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert sent_sms == []


def test_no_alert_when_green(db, sim_farm, fake_et, twilio_settings, sms_farmer, sent_sms, monkeypatch):
    _force_sim_severity(monkeypatch, StressSeverity.GREEN)

    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert sent_sms == []


def test_alert_rerun_is_idempotent(db, sim_farm, fake_et, twilio_settings, sms_farmer, sent_sms, monkeypatch):
    """First-ever output counts as escalation (no previous = green); the
    re-run dedupes on the existing Alert row."""
    _force_sim_severity(monkeypatch, StressSeverity.YELLOW)

    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    asyncio.run(run_et_sim_job(db=db, today=TODAY))

    assert len(sent_sms) == 1
    assert db.query(models.Alert).count() == 1


def test_no_alert_without_opt_in(db, sim_farm, fake_et, twilio_settings, user, sent_sms, monkeypatch):
    user.phone_number = "+15551112222"  # phone on file but alerts not enabled
    db.commit()
    _force_sim_severity(monkeypatch, StressSeverity.RED)

    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert sent_sms == []
    assert db.query(models.Alert).count() == 0


def test_no_alert_when_twilio_unconfigured(db, sim_farm, fake_et, sms_farmer, sent_sms, monkeypatch):
    monkeypatch.setattr(settings, "twilio_account_sid", None)
    monkeypatch.setattr(settings, "twilio_auth_token", None)
    monkeypatch.setattr(settings, "twilio_from_number", None)
    _force_sim_severity(monkeypatch, StressSeverity.RED)

    asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert sent_sms == []


def test_alert_send_failure_does_not_fail_job(db, sim_farm, fake_et, twilio_settings, sms_farmer, monkeypatch):
    async def twilio_down(to, body, transport=None):
        raise SmsError("Twilio returned 503")

    monkeypatch.setattr(sms_service, "send_sms", twilio_down)
    _force_sim_severity(monkeypatch, StressSeverity.RED)

    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_processed == 1
    assert "alert send failed" in job_run.detail
    # no Alert row — tomorrow's run can try again
    assert db.query(models.Alert).count() == 0


# ── savings job ──────────────────────────────────────────────────────────────


def _seed_savings_inputs(db, farm_id):
    crud.create_baseline_irrigation(db, farm_id, BaselineIrrigationCreate(gallons_per_week_estimate=Decimal("7000")))
    crud.create_irrigation_event(db, farm_id, IrrigationEventCreate(event_date=date(2026, 6, 2), gallons_applied=Decimal("2500")))
    crud.create_irrigation_event(db, farm_id, IrrigationEventCreate(event_date=date(2026, 6, 5), gallons_applied=Decimal("1500")))
    # outside the period — must not count
    crud.create_irrigation_event(db, farm_id, IrrigationEventCreate(event_date=date(2026, 6, 8), gallons_applied=Decimal("9999")))


def test_savings_job_computes_week(db, sim_farm):
    _seed_savings_inputs(db, sim_farm.id)
    job_run = run_savings_job(db=db, today=TODAY)

    assert job_run.job_name == SAVINGS_JOB_NAME
    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_processed == 1
    row = db.query(models.WaterSavings).filter_by(farm_id=sim_farm.id).one()
    assert (row.period_start, row.period_end) == (date(2026, 6, 1), date(2026, 6, 7))
    assert row.baseline_gallons == Decimal("7000.00")
    assert row.actual_gallons == Decimal("4000.00")
    assert row.gallons_saved == Decimal("3000.00")
    assert row.kwh_saved == Decimal("1.71")  # 3000 gal x 100 ft lift at 55% efficiency
    assert row.co2_kg_saved == Decimal("0.39")


def test_savings_job_upsert_idempotent(db, sim_farm):
    _seed_savings_inputs(db, sim_farm.id)
    run_savings_job(db=db, today=TODAY)
    crud.create_irrigation_event(db, sim_farm.id, IrrigationEventCreate(event_date=date(2026, 6, 6), gallons_applied=Decimal("1000")))
    run_savings_job(db=db, today=TODAY)

    rows = db.query(models.WaterSavings).filter_by(farm_id=sim_farm.id).all()
    assert len(rows) == 1
    assert rows[0].actual_gallons == Decimal("5000.00")  # late-logged event picked up
    assert rows[0].gallons_saved == Decimal("2000.00")


def test_savings_job_negative_savings_kept(db, sim_farm):
    crud.create_baseline_irrigation(db, sim_farm.id, BaselineIrrigationCreate(gallons_per_week_estimate=Decimal("1000")))
    crud.create_irrigation_event(db, sim_farm.id, IrrigationEventCreate(event_date=date(2026, 6, 3), gallons_applied=Decimal("4000")))
    run_savings_job(db=db, today=TODAY)

    row = db.query(models.WaterSavings).filter_by(farm_id=sim_farm.id).one()
    assert row.gallons_saved == Decimal("-3000.00")
    assert row.kwh_saved < 0
    assert row.co2_kg_saved < 0


def test_savings_job_skips_farm_without_baseline(db, sim_farm):
    job_run = run_savings_job(db=db, today=TODAY)
    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_skipped == 1
    assert "no baseline" in job_run.detail
    assert db.query(models.WaterSavings).count() == 0


def test_savings_job_no_pump_lift_zero_energy(db, user):
    farm = crud.create_farm(db, FarmCreate(name="No pump", planting_date=START), user_id=user.id)
    crud.create_baseline_irrigation(db, farm.id, BaselineIrrigationCreate(gallons_per_week_estimate=Decimal("7000")))
    crud.create_irrigation_event(db, farm.id, IrrigationEventCreate(event_date=date(2026, 6, 2), gallons_applied=Decimal("2000")))
    run_savings_job(db=db, today=TODAY)

    row = db.query(models.WaterSavings).filter_by(farm_id=farm.id).one()
    assert row.gallons_saved == Decimal("5000.00")
    assert row.kwh_saved == Decimal("0.00")
    assert row.co2_kg_saved == Decimal("0.00")


def test_savings_job_skips_week_with_no_logged_events(db, sim_farm):
    """Grant integrity: silence must not book the whole baseline as savings."""
    crud.create_baseline_irrigation(db, sim_farm.id, BaselineIrrigationCreate(gallons_per_week_estimate=Decimal("7000")))
    job_run = run_savings_job(db=db, today=TODAY)

    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_skipped == 1
    assert "no irrigation logged" in job_run.detail
    assert db.query(models.WaterSavings).count() == 0


# ── failure paths + session ownership ────────────────────────────────────────


def test_et_sim_job_sim_failure_counts_farm(db, user, fake_et):
    # passes the config check (crop set) but the runner rejects the crop type
    crud.create_farm(db, FarmCreate(
        name="Bad crop", crop_type="dragonfruit", soil_type=SoilTexture.SandyLoam,
        planting_date=START, field_polygon=FIELD_WKT,
    ), user_id=user.id)
    job_run = asyncio.run(run_et_sim_job(db=db, today=TODAY))
    assert job_run.status == JobStatus.FAILED
    assert job_run.farms_failed == 1
    assert "sim failed" in job_run.detail


def test_et_sim_job_unhandled_crash_records_failure(db, sim_farm, monkeypatch):
    monkeypatch.setattr(crud, "get_active_farms", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(run_et_sim_job(db=db, today=TODAY))
    job_run = db.query(models.JobRun).filter_by(job_name=ET_SIM_JOB_NAME).one()
    assert job_run.status == JobStatus.FAILED
    assert "unhandled: boom" in job_run.detail


def test_savings_job_per_farm_error_continues(db, sim_farm, monkeypatch):
    crud.create_baseline_irrigation(db, sim_farm.id, BaselineIrrigationCreate(gallons_per_week_estimate=Decimal("7000")))
    crud.create_irrigation_event(db, sim_farm.id, IrrigationEventCreate(event_date=date(2026, 6, 2), gallons_applied=Decimal("1000")))
    monkeypatch.setattr(crud, "sum_irrigation_gallons", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db hiccup")))
    job_run = run_savings_job(db=db, today=TODAY)
    assert job_run.status == JobStatus.FAILED
    assert job_run.farms_failed == 1
    assert "savings failed" in job_run.detail


def test_savings_job_unhandled_crash_records_failure(db, monkeypatch):
    from backend.services import scheduler as scheduler_module
    monkeypatch.setattr(scheduler_module.savings_calculator, "last_completed_week", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError, match="boom"):
        run_savings_job(db=db, today=TODAY)
    job_run = db.query(models.JobRun).filter_by(job_name=SAVINGS_JOB_NAME).one()
    assert job_run.status == JobStatus.FAILED


def test_jobs_open_and_close_their_own_session(db, sim_farm, fake_et, monkeypatch):
    from backend.services import scheduler as scheduler_module
    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: db)
    et_run = asyncio.run(run_et_sim_job())
    savings_run = run_savings_job()
    satellite_run = run_satellite_scans_job()
    assert et_run.id is not None
    assert savings_run.id is not None
    assert satellite_run.id is not None


# ── Sentinel satellite scan job ───────────────────────────────────────────────


def test_satellite_job_upserts_and_dedupes(db, sim_farm, monkeypatch):
    monkeypatch.setattr(settings, "sentinel_enabled", True)
    run_satellite_scans_job(db=db, today=TODAY)
    run_satellite_scans_job(db=db, today=TODAY)

    rows = crud.get_satellite_scans_by_farm(db, sim_farm.id, limit=100)
    assert len(rows) == 1
    assert rows[0].scan_date == TODAY
    assert float(rows[0].mean_ndvi) == pytest.approx(0.61)
    assert rows[0].source == "sentinel2"
    full = crud.get_satellite_scan(db, sim_farm.id, rows[0].id)
    assert full.ndvi_grid_bounds == [[36.9, -120.1], [36.91, -120.09]]


def test_satellite_job_per_farm_failure_does_not_block_others(db, user, monkeypatch):
    farm_ok = crud.create_farm(
        db,
        FarmCreate(
            name="OK",
            crop_type="corn",
            soil_type=SoilTexture.SandyLoam,
            planting_date=START,
            field_polygon=FIELD_WKT,
        ),
        user_id=user.id,
    )
    farm_fail = crud.create_farm(
        db,
        FarmCreate(
            name="Fail",
            crop_type="corn",
            soil_type=SoilTexture.SandyLoam,
            planting_date=START,
            field_polygon=FIELD_WKT,
        ),
        user_id=user.id,
    )
    monkeypatch.setattr(settings, "sentinel_enabled", True)

    def flaky_fetch(polygon, max_cloud_pct=15, lookback_days=14):
        if flaky_fetch.calls == 0:
            flaky_fetch.calls += 1
            return {
                "scan_date": TODAY,
                "cloud_cover_pct": 4.2,
                "mean_ndvi": 0.61,
                "max_ndvi": 0.78,
                "min_ndvi": 0.41,
                "ndvi_grid": [[0.5]],
                "ndvi_grid_bounds": [[36.9, -120.1], [36.91, -120.09]],
            }
        raise SentinelUnavailableError("no scene")

    flaky_fetch.calls = 0
    monkeypatch.setattr(sentinel_client, "fetch_latest_ndvi", flaky_fetch)
    job_run = run_satellite_scans_job(db=db, today=TODAY)
    assert job_run.status == JobStatus.FAILED
    assert job_run.farms_processed == 1
    assert job_run.farms_failed == 1
    assert "sentinel fetch failed" in (job_run.detail or "")
    assert crud.count_satellite_scans_by_farm(db, farm_ok.id) + crud.count_satellite_scans_by_farm(db, farm_fail.id) == 1


def test_satellite_job_disabled_is_noop(db, sim_farm, monkeypatch):
    monkeypatch.setattr(settings, "sentinel_enabled", False)
    job_run = run_satellite_scans_job(db=db, today=TODAY)
    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_processed == 0
    assert crud.count_satellite_scans_by_farm(db, sim_farm.id) == 0


def test_satellite_job_scans_active_farms_only(db, user, fake_satellite, monkeypatch):
    monkeypatch.setattr(settings, "sentinel_enabled", True)
    no_polygon = crud.create_farm(
        db,
        FarmCreate(
            name="No Polygon",
            crop_type="corn",
            soil_type=SoilTexture.SandyLoam,
            planting_date=START,
        ),
        user_id=user.id,
    )
    unplanted = crud.create_farm(
        db,
        FarmCreate(name="Unplanted", field_polygon=FIELD_WKT),
        user_id=user.id,
    )
    job_run = run_satellite_scans_job(db=db, today=TODAY)
    assert job_run.status == JobStatus.SUCCESS
    assert job_run.farms_processed == 0
    assert job_run.farms_skipped == 1  # active but missing polygon
    assert "missing polygon" in (job_run.detail or "")
    assert len(fake_satellite) == 0  # unplanted farm never fetched
    assert crud.count_satellite_scans_by_farm(db, no_polygon.id) == 0
    assert crud.count_satellite_scans_by_farm(db, unplanted.id) == 0


# ── scheduler lifecycle ──────────────────────────────────────────────────────


def test_start_and_shutdown_scheduler():
    from backend.services import scheduler as scheduler_module

    async def lifecycle():
        s = scheduler_module.start_scheduler()
        try:
            assert s.running
            assert {job.id for job in s.get_jobs()} == {
                ET_SIM_JOB_NAME,
                SAVINGS_JOB_NAME,
                SATELLITE_SCANS_JOB_NAME,
                scheduler_module.REGIONAL_STATS_JOB_NAME,
            }
            assert scheduler_module.start_scheduler() is s  # idempotent
        finally:
            scheduler_module.shutdown_scheduler()
        assert scheduler_module._scheduler is None
        scheduler_module.shutdown_scheduler()  # no-op when already stopped

    asyncio.run(lifecycle())


# ── stale guard surfaced in API ──────────────────────────────────────────────


def _cached_output(db, farm_id, as_of):
    return crud.upsert_aquacrop_output(db, farm_id, AquaCropOutputBase(
        as_of_date=as_of,
        depletion_mm=Decimal("30.00"),
        root_zone_moisture_pct=Decimal("70.00"),
        severity=None,
        days_to_stress=None,
        paw_mm=Decimal("80.00"),
        raw_threshold_mm=Decimal("76.00"),
    ))


def test_water_stress_reports_fresh_et(client, db, farm):
    recent = date.today() - timedelta(days=2)
    _cached_output(db, farm.id, recent)
    crud.create_et_readings(db, [ETReadingCreate(farm_id=farm.id, reading_date=recent, et_mm=5.0, source=ET_SOURCE)])

    body = client.get(f"/farms/{farm.id}/water-stress").json()
    assert body["et_latest_date"] == recent.isoformat()
    assert body["et_is_stale"] is False


def test_water_stress_reports_stale_et(client, db, farm):
    old = date.today() - timedelta(days=20)
    _cached_output(db, farm.id, old)
    crud.create_et_readings(db, [ETReadingCreate(farm_id=farm.id, reading_date=old, et_mm=5.0, source=ET_SOURCE)])

    body = client.get(f"/farms/{farm.id}/water-stress").json()
    assert body["et_latest_date"] == old.isoformat()
    assert body["et_is_stale"] is True


def test_water_stress_no_et_readings_is_stale(client, db, farm):
    _cached_output(db, farm.id, date.today())
    body = client.get(f"/farms/{farm.id}/water-stress").json()
    assert body["et_latest_date"] is None
    assert body["et_is_stale"] is True
