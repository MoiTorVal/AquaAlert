import asyncio
from datetime import date, timedelta
from decimal import Decimal

import pytest

from backend import crud, models
from backend.enums import JobStatus, SoilTexture
from backend.schemas import AquaCropOutputBase, BaselineIrrigationCreate, ETReadingCreate, FarmCreate, IrrigationEventCreate
from backend.services import openet_client, savings_calculator
from backend.services.openet_client import ET_SOURCE, OpenETRateLimitError, OpenETUnavailableError
from backend.services.scheduler import (
    ET_SIM_JOB_NAME,
    SAVINGS_JOB_NAME,
    is_et_stale,
    run_et_sim_job,
    run_savings_job,
)

START = date(2026, 5, 1)
TODAY = date(2026, 6, 9)  # a Tuesday; last completed week = Jun 1 - Jun 7
FIELD_WKT = "POLYGON((-120.1 36.9, -120.1 36.91, -120.09 36.91, -120.09 36.9, -120.1 36.9))"


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
    run_savings_job(db=db, today=TODAY)

    row = db.query(models.WaterSavings).filter_by(farm_id=farm.id).one()
    assert row.gallons_saved == Decimal("7000.00")
    assert row.kwh_saved == Decimal("0.00")
    assert row.co2_kg_saved == Decimal("0.00")


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
    assert et_run.id is not None
    assert savings_run.id is not None


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
