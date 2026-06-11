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
from backend.enums import JobStatus, StressSeverity
from backend.schemas import ETReadingCreate, WaterSavingsBase
from backend.services import cimis_client, openet_client, savings_calculator, sms_service
from backend.services.aquacrop_runner import AquaCropInputError, compute_and_cache_water_stress
from backend.services.cimis_client import CimisError
from backend.services.openet_client import ET_SOURCE, OpenETError, OpenETRateLimitError
from backend.services.sms_service import SmsError

logger = logging.getLogger(__name__)

ET_SIM_JOB_NAME = "daily_et_sim"
SAVINGS_JOB_NAME = "daily_water_savings"
REGIONAL_STATS_JOB_NAME = "nightly_regional_stats"
STALE_ET_DAYS = 7

# Provisional gap-fill rows: Spatial CIMIS reference ET scaled by a crop
# coefficient. Replaced in place by OpenET actuals as they land.
PROVISIONAL_ET_SOURCE = "cimis:eto*kc"

# FAO-56 Table 12 mid-season Kc (midpoint where the table gives a range;
# quinoa is absent from FAO-56 — literature consensus ~1.00). Mid-season-only
# is a documented simplification: the gap window is <= ~7 days, and the Phase 9
# residual model absorbs stage-curve error. Keys must mirror
# aquacrop_runner.CROP_TYPE_TO_AQUACROP (enforced by test).
KC_MID = {
    "alfalfa": 0.95,
    "barley": 1.15,
    "cassava": 0.80,
    "corn": 1.20,
    "cotton": 1.18,
    "drybean": 1.15,
    "maize": 1.20,
    "potato": 1.15,
    "quinoa": 1.00,
    "rice": 1.20,
    "sorghum": 1.05,
    "soybean": 1.15,
    "sugarbeet": 1.20,
    "sunflower": 1.08,
    "tomato": 1.15,
    "wheat": 1.15,
}

SEVERITY_RANK = {StressSeverity.GREEN: 0, StressSeverity.YELLOW: 1, StressSeverity.RED: 2}

_scheduler: AsyncIOScheduler | None = None


def is_et_stale(latest_et_date: date | None, today: date | None = None) -> bool:
    """Stale-data guard: no fresh ET within STALE_ET_DAYS (OpenET lag is ~5-7d)."""
    if today is None:
        today = date.today()
    return latest_et_date is None or latest_et_date < today - timedelta(days=STALE_ET_DAYS)


async def _pull_et_for_farm(db: Session, farm: models.Farm, today: date) -> None:
    """Fetch only the dates missing since the last cached reading (quota-frugal).

    Keyed to the latest OpenET-source row — provisional gap-fill rows sit past
    it and must be refetched (upsert replaces them) once actuals exist.
    """
    latest = crud.get_latest_et_date(db, farm.id, source=ET_SOURCE)
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
        crud.upsert_et_readings(db, new_readings)


async def _gapfill_et_for_farm(db: Session, farm: models.Farm, today: date) -> int:
    """Bridge the OpenET lag window with provisional CIMIS ETo x Kc readings.

    Best-effort: requires a CIMIS key and a supported crop, fills only dates
    with no reading at all (never overwrites actuals), and stops at yesterday
    (Spatial CIMIS publishes with ~1-day lag). Returns rows attempted.
    """
    if settings.cimis_app_key is None:
        return 0
    kc = KC_MID.get((farm.crop_type or "").strip().lower())
    if kc is None:
        return 0
    latest = crud.get_latest_et_date(db, farm.id)
    if latest is None:
        return 0
    gap_start = latest + timedelta(days=1)
    gap_end = today - timedelta(days=1)
    if gap_start > gap_end:
        return 0
    centroid = to_shape(farm.field_polygon).centroid
    points = await cimis_client.fetch_daily_eto(centroid.y, centroid.x, gap_start, gap_end)
    readings = [
        ETReadingCreate(
            farm_id=farm.id,
            reading_date=p["reading_date"],
            et_mm=round(p["eto_mm"] * kc, 2),
            source=PROVISIONAL_ET_SOURCE,
        )
        for p in points
    ]
    crud.insert_et_readings_if_absent(db, readings)
    return len(readings)


async def _maybe_send_stress_alert(db: Session, farm: models.Farm, output: models.AquaCropOutput) -> bool:
    """Text the farmer when severity escalates vs the previous sim day.

    Escalation-only (green->yellow, ->red, yellow->red) so a farm sitting at
    red doesn't text every day; after irrigation drops it back to green the
    next climb alerts again. The (farm, as_of_date, severity) unique row keeps
    a crashed-job re-run from sending twice.
    """
    if not sms_service.is_configured():
        return False
    if output.severity is None or SEVERITY_RANK[output.severity] == 0:
        return False
    user = db.get(models.User, farm.user_id)
    if user is None or user.phone_number is None or not user.sms_alerts_enabled:
        return False
    previous = crud.get_previous_severity(db, farm.id, before_date=output.as_of_date)
    if SEVERITY_RANK[output.severity] <= SEVERITY_RANK.get(previous, 0):
        return False
    if crud.get_alert(db, farm.id, output.as_of_date, output.severity) is not None:
        return False
    body = sms_service.stress_alert_body(
        user.locale, farm.name, output.severity, output.as_of_date, output.days_to_stress
    )
    sid = await sms_service.send_sms(user.phone_number, body)
    crud.create_alert(
        db, farm_id=farm.id, severity=output.severity, as_of_date=output.as_of_date,
        days_to_stress=output.days_to_stress, provider_message_sid=sid,
    )
    return True


async def run_et_sim_job(db: Session | None = None, today: date | None = None) -> models.JobRun:
    """Daily: per active farm, pull missing OpenET days, run AquaCrop, cache output."""
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    if today is None:
        today = date.today()
    job_run = crud.create_job_run(db, ET_SIM_JOB_NAME)
    processed = failed = skipped = alerts_sent = 0
    stale_farms: list[int] = []
    provisional_only_farms: list[int] = []
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

            # Best-effort: a CIMIS outage must never fail the farm — the sim
            # just runs on actuals alone, as it did before gap-fill existed.
            try:
                await _gapfill_et_for_farm(db, farm, today)
            except CimisError as exc:
                notes.append(f"farm {farm.id}: CIMIS gap-fill failed: {exc}")
                logger.warning("CIMIS gap-fill failed for farm %d: %s", farm.id, exc)

            latest = crud.get_latest_et_date(db, farm.id)
            if latest is None:
                skipped += 1
                notes.append(f"farm {farm.id}: no ET data available")
                continue
            if is_et_stale(latest, today):
                stale_farms.append(farm.id)
                logger.warning("Stale ET for farm %d: latest reading %s", farm.id, latest)
            elif is_et_stale(crud.get_latest_et_date(db, farm.id, source=ET_SOURCE), today):
                # Fresh only thanks to provisional rows — surface it so a
                # broken OpenET pull can't hide behind CIMIS indefinitely.
                provisional_only_farms.append(farm.id)
            try:
                output = compute_and_cache_water_stress(db, farm, as_of_date=latest)
            except AquaCropInputError as exc:
                failed += 1
                notes.append(f"farm {farm.id}: sim failed: {exc}")
                logger.warning("AquaCrop sim failed for farm %d: %s", farm.id, exc)
                continue
            # Alert delivery is best-effort: a Twilio outage must not mark the
            # sim as failed — the cached result is already correct.
            try:
                if await _maybe_send_stress_alert(db, farm, output):
                    alerts_sent += 1
            except SmsError as exc:
                notes.append(f"farm {farm.id}: alert send failed: {exc}")
                logger.warning("Alert send failed for farm %d: %s", farm.id, exc)
            processed += 1

        if stale_farms:
            notes.append(f"stale ET (> {STALE_ET_DAYS}d): farms {stale_farms}")
        if provisional_only_farms:
            notes.append(f"OpenET actuals stale, running on provisional ET: farms {provisional_only_farms}")
        if alerts_sent:
            notes.append(f"alerts sent: {alerts_sent}")
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
