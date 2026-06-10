"""APScheduler instance + daily jobs: ET pull → AquaCrop sim, and weekly savings.

Jobs are idempotent — ET inserts skip already-cached dates, sims and savings
upsert on their unique constraints — so a re-run after a crash is safe.
Every run writes a JobRun row for observability.

Deploy constraint: APScheduler holds no cross-process lock. Enable via
SCHEDULER_ENABLED=true on exactly one single-worker process, or every worker
runs every job.
"""
import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from backend import crud, models
from backend.config import settings
from backend.database import SessionLocal
from backend.enums import JobStatus
from backend.schemas import ETReadingCreate, WaterSavingsBase
from backend.services import openet_client, savings_calculator
from backend.services.aquacrop_runner import AquaCropInputError, compute_and_cache_water_stress
from backend.services.openet_client import ET_SOURCE, OpenETError, OpenETRateLimitError

logger = logging.getLogger(__name__)

ET_SIM_JOB_NAME = "daily_et_sim"
SAVINGS_JOB_NAME = "daily_water_savings"
REGIONAL_STATS_JOB_NAME = "nightly_regional_stats"
STALE_ET_DAYS = 7

_scheduler: AsyncIOScheduler | None = None


def is_et_stale(latest_et_date: date | None, today: date | None = None) -> bool:
    """Stale-data guard: no fresh ET within STALE_ET_DAYS (OpenET lag is ~5-7d)."""
    if today is None:
        today = date.today()
    return latest_et_date is None or latest_et_date < today - timedelta(days=STALE_ET_DAYS)


async def _pull_et_for_farm(db: Session, farm: models.Farm, today: date) -> None:
    """Fetch only the dates missing since the last cached reading (quota-frugal)."""
    latest = crud.get_latest_et_date(db, farm.id)
    fetch_start = farm.planting_date if latest is None else latest + timedelta(days=1)
    if fetch_start > today:
        return
    geometry = openet_client.polygon_to_geometry(to_shape(farm.field_polygon))
    points = await openet_client.fetch_daily_et(geometry, fetch_start, today)
    points = openet_client.trim_gapfill_tail(points, today=today)
    new_readings = [
        ETReadingCreate(
            farm_id=farm.id,
            reading_date=p["reading_date"],
            et_mm=p["et_mm"],
            source=ET_SOURCE,
        )
        for p in points
        if p["reading_date"] >= fetch_start
    ]
    if new_readings:
        crud.create_et_readings(db, new_readings)


async def run_et_sim_job(db: Session | None = None, today: date | None = None) -> models.JobRun:
    """Daily: per active farm, pull missing OpenET days, run AquaCrop, cache output."""
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    if today is None:
        today = date.today()
    job_run = crud.create_job_run(db, ET_SIM_JOB_NAME)
    processed = failed = skipped = 0
    stale_farms: list[int] = []
    notes: list[str] = []
    try:
        for farm in crud.get_active_farms(db, today):
            if farm.field_polygon is None or farm.crop_type is None or farm.soil_type is None:
                skipped += 1
                notes.append(f"farm {farm.id}: missing polygon/crop/soil")
                continue
            try:
                await _pull_et_for_farm(db, farm, today)
            except OpenETRateLimitError as exc:
                # Monthly quota exhausted — every remaining farm would fail too.
                notes.append(f"quota exhausted at farm {farm.id}: {exc}")
                crud.finish_job_run(
                    db, job_run, JobStatus.FAILED,
                    processed=processed, failed=failed + 1, skipped=skipped,
                    detail="; ".join(notes)[:2000],
                )
                return job_run
            except OpenETError as exc:
                failed += 1
                notes.append(f"farm {farm.id}: ET fetch failed: {exc}")
                logger.warning("ET fetch failed for farm %d: %s", farm.id, exc)
                continue

            latest = crud.get_latest_et_date(db, farm.id)
            if latest is None:
                skipped += 1
                notes.append(f"farm {farm.id}: no ET data available")
                continue
            if is_et_stale(latest, today):
                stale_farms.append(farm.id)
                logger.warning("Stale ET for farm %d: latest reading %s", farm.id, latest)
            try:
                compute_and_cache_water_stress(db, farm, as_of_date=latest)
            except AquaCropInputError as exc:
                failed += 1
                notes.append(f"farm {farm.id}: sim failed: {exc}")
                logger.warning("AquaCrop sim failed for farm %d: %s", farm.id, exc)
                continue
            processed += 1

        if stale_farms:
            notes.append(f"stale ET (> {STALE_ET_DAYS}d): farms {stale_farms}")
        status = JobStatus.SUCCESS if failed == 0 else JobStatus.FAILED
        crud.finish_job_run(
            db, job_run, status,
            processed=processed, failed=failed, skipped=skipped,
            detail="; ".join(notes)[:2000] or None,
        )
        return job_run
    except Exception as exc:
        logger.exception("%s crashed", ET_SIM_JOB_NAME)
        crud.finish_job_run(
            db, job_run, JobStatus.FAILED,
            processed=processed, failed=failed, skipped=skipped,
            detail=f"unhandled: {exc}"[:2000],
        )
        raise
    finally:
        if owns_session:
            db.close()


def run_savings_job(db: Session | None = None, today: date | None = None) -> models.JobRun:
    """Daily: recompute last completed week's savings per farm (catches late-logged events).

    WaterSavings rows are written here and only here — route handlers never
    write them (CLAUDE.md invariant).
    """
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    if today is None:
        today = date.today()
    job_run = crud.create_job_run(db, SAVINGS_JOB_NAME)
    processed = failed = skipped = 0
    notes: list[str] = []
    try:
        period_start, period_end = savings_calculator.last_completed_week(today)
        for farm in crud.get_active_farms(db, today):
            baseline = crud.get_latest_baseline_irrigation(db, farm.id)
            if baseline is None:
                skipped += 1
                notes.append(f"farm {farm.id}: no baseline")
                continue
            # Grant-report integrity: a week with no logged irrigation would
            # book the full baseline as "saved" — a farmer who stops using the
            # app would generate maximum savings. Skip the week instead.
            if crud.count_irrigation_events_by_farm(
                db, farm.id, start_date=period_start, end_date=period_end
            ) == 0:
                skipped += 1
                notes.append(f"farm {farm.id}: no irrigation logged this week")
                continue
            try:
                actual = crud.sum_irrigation_gallons(db, farm.id, period_start, period_end)
                gallons_saved = baseline.gallons_per_week_estimate - actual
                kwh_saved = savings_calculator.gallons_to_kwh(gallons_saved, farm.pump_lift_ft)
                crud.upsert_water_savings(db, farm.id, WaterSavingsBase(
                    period_start=period_start,
                    period_end=period_end,
                    baseline_gallons=baseline.gallons_per_week_estimate,
                    actual_gallons=actual,
                    gallons_saved=gallons_saved,
                    kwh_saved=kwh_saved,
                    co2_kg_saved=savings_calculator.kwh_to_co2_kg(kwh_saved),
                ))
            except Exception as exc:
                failed += 1
                notes.append(f"farm {farm.id}: savings failed: {exc}")
                logger.warning("Savings compute failed for farm %d: %s", farm.id, exc)
                continue
            processed += 1

        status = JobStatus.SUCCESS if failed == 0 else JobStatus.FAILED
        crud.finish_job_run(
            db, job_run, status,
            processed=processed, failed=failed, skipped=skipped,
            detail="; ".join(notes)[:2000] or None,
        )
        return job_run
    except Exception as exc:
        logger.exception("%s crashed", SAVINGS_JOB_NAME)
        crud.finish_job_run(
            db, job_run, JobStatus.FAILED,
            processed=processed, failed=failed, skipped=skipped,
            detail=f"unhandled: {exc}"[:2000],
        )
        raise
    finally:
        if owns_session:
            db.close()


def run_regional_stats_job(db: Session | None = None, today: date | None = None) -> models.JobRun:
    """Nightly: aggregate cohort stats for the public /impact dashboard.

    Aggregates only — counts and sums, no farm-identifiable or equity data.
    """
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    if today is None:
        today = date.today()
    job_run = crud.create_job_run(db, REGIONAL_STATS_JOB_NAME)
    try:
        severity = crud.count_farms_by_severity(db)
        gallons, kwh, co2 = crud.sum_all_water_savings(db)
        total_farms = db.query(models.Farm).count()
        crud.upsert_regional_stats(db, snapshot_date=today, values={
            "total_farms": total_farms,
            "farms_green": severity["green"],
            "farms_yellow": severity["yellow"],
            "farms_red": severity["red"],
            "total_gallons_saved": gallons,
            "total_kwh_saved": kwh,
            "total_co2_kg_saved": co2,
        })
        crud.finish_job_run(db, job_run, JobStatus.SUCCESS, processed=total_farms)
        return job_run
    except Exception as exc:
        logger.exception("%s crashed", REGIONAL_STATS_JOB_NAME)
        crud.finish_job_run(db, job_run, JobStatus.FAILED, detail=f"unhandled: {exc}"[:2000])
        raise
    finally:
        if owns_session:
            db.close()


def start_scheduler() -> AsyncIOScheduler:
    """Start the daily jobs. ET+sim at 02:00, savings at 03:00 (after ET lands)."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler
    _scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    _scheduler.add_job(run_et_sim_job, CronTrigger(hour=2, minute=0), id=ET_SIM_JOB_NAME)
    # sync jobs: APScheduler runs them in worker threads, off the event loop
    _scheduler.add_job(run_savings_job, CronTrigger(hour=3, minute=0), id=SAVINGS_JOB_NAME)
    # after the savings job so public totals include today's rows
    _scheduler.add_job(run_regional_stats_job, CronTrigger(hour=4, minute=0), id=REGIONAL_STATS_JOB_NAME)
    _scheduler.start()
    logger.info("Scheduler started (%s, %s)", ET_SIM_JOB_NAME, SAVINGS_JOB_NAME)
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _scheduler = None
