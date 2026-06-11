from backend import models
from backend.schemas import (
    FarmCreate, FarmUpdate, WeatherReadingCreate, IrrigationEventCreate, BaselineIrrigationCreate,
    ETReadingCreate, AquaCropOutputBase, WaterSavingsBase,
)
from backend.enums import AlertFeedback, IrrigationSource, JobStatus, StressSeverity
from decimal import Decimal
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, Query
from datetime import datetime, date


def _wrap_field_polygon(data: dict) -> dict:
    if data.get("field_polygon") is not None:
        data["field_polygon"] = WKTElement(data["field_polygon"], srid=4326)
    return data


# CRUD operations for farms
def create_farm(db: Session, farm: FarmCreate, user_id: int) -> models.Farm:
    db_farm = models.Farm(**_wrap_field_polygon(farm.model_dump()), user_id=user_id)
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm

def get_farm(db: Session, farm_id: int) -> models.Farm | None:
    return db.query(models.Farm).filter(models.Farm.id == farm_id).first()

def get_farms(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> list[models.Farm]:
    return db.query(models.Farm).filter(models.Farm.user_id == user_id).offset(skip).limit(limit).all()

def delete_farm(db: Session, farm: models.Farm) -> models.Farm:
    db.delete(farm)
    db.commit()
    return farm

def update_farm(db: Session, farm: models.Farm, farm_update: FarmUpdate) -> models.Farm:
    for key, value in _wrap_field_polygon(farm_update.model_dump(exclude_unset=True)).items():
        setattr(farm, key, value)
    db.commit()
    db.refresh(farm)
    return farm

def create_weather_reading(db: Session, weather_reading: WeatherReadingCreate) -> models.WeatherReading:
    db_weather_reading = models.WeatherReading(**weather_reading.model_dump())
    db.add(db_weather_reading)
    db.commit()
    db.refresh(db_weather_reading)
    return db_weather_reading

def _weather_readings_base_query(db: Session, farm_id: int, start_date: datetime | None, end_date: datetime | None) -> Query:
    query = db.query(models.WeatherReading).filter(models.WeatherReading.farm_id == farm_id)
    if start_date:
        query = query.filter(models.WeatherReading.recorded_at >= start_date)
    if end_date:
        query = query.filter(models.WeatherReading.recorded_at <= end_date)
    return query


def get_weather_readings_by_farm(
    db: Session,
    farm_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[models.WeatherReading]:
    return (
        _weather_readings_base_query(db, farm_id, start_date, end_date)
        .order_by(models.WeatherReading.recorded_at)
        .offset(skip)
        .limit(limit)
        .all()
    )

def count_weather_readings_by_farm(
    db: Session,
    farm_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> int:
    return _weather_readings_base_query(db, farm_id, start_date, end_date).count()


def create_irrigation_event(
    db: Session,
    farm_id: int,
    event: IrrigationEventCreate,
    source: IrrigationSource = IrrigationSource.USER_LOG,
) -> models.IrrigationEvent:
    db_event = models.IrrigationEvent(
        **event.model_dump(),
        farm_id=farm_id,
        source=source,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_latest_irrigation_event(db: Session, farm_id: int) -> models.IrrigationEvent | None:
    return (
        db.query(models.IrrigationEvent)
        .filter(models.IrrigationEvent.farm_id == farm_id)
        .order_by(models.IrrigationEvent.event_date.desc(), models.IrrigationEvent.logged_at.desc())
        .first()
    )


def _irrigation_events_base_query(db: Session, farm_id: int, start_date: date | None, end_date: date | None) -> Query:
    query = db.query(models.IrrigationEvent).filter(models.IrrigationEvent.farm_id == farm_id)
    if start_date:
        query = query.filter(models.IrrigationEvent.event_date >= start_date)
    if end_date:
        query = query.filter(models.IrrigationEvent.event_date <= end_date)
    return query


def get_irrigation_events_by_farm(
    db: Session,
    farm_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[models.IrrigationEvent]:
    return (
        _irrigation_events_base_query(db, farm_id, start_date, end_date)
        .order_by(models.IrrigationEvent.event_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_irrigation_events_by_farm(
    db: Session,
    farm_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> int:
    return _irrigation_events_base_query(db, farm_id, start_date, end_date).count()


def get_et_readings_by_farm(
    db: Session,
    farm_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[models.ETReading]:
    query = db.query(models.ETReading).filter(models.ETReading.farm_id == farm_id)
    if start_date:
        query = query.filter(models.ETReading.reading_date >= start_date)
    if end_date:
        query = query.filter(models.ETReading.reading_date <= end_date)
    return query.order_by(models.ETReading.reading_date).all()


def create_et_readings(db: Session, readings: list[ETReadingCreate]) -> list[models.ETReading]:
    rows = [models.ETReading(**reading.model_dump()) for reading in readings]
    db.add_all(rows)
    db.commit()
    return rows


def upsert_et_readings(db: Session, readings: list[ETReadingCreate]) -> None:
    """Insert readings, replacing any existing row for the same farm/date —
    used when OpenET actuals land on dates holding provisional gap-fill values."""
    if not readings:
        return
    stmt = pg_insert(models.ETReading).values([r.model_dump() for r in readings])
    stmt = stmt.on_conflict_do_update(
        constraint="uq_et_farm_date",
        set_={
            "et_mm": stmt.excluded.et_mm,
            "source": stmt.excluded.source,
            "fetched_at": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()


def insert_et_readings_if_absent(db: Session, readings: list[ETReadingCreate]) -> None:
    """Insert readings, never touching existing rows — provisional gap-fill
    values must not overwrite OpenET actuals."""
    if not readings:
        return
    stmt = (
        pg_insert(models.ETReading)
        .values([r.model_dump() for r in readings])
        .on_conflict_do_nothing(constraint="uq_et_farm_date")
    )
    db.execute(stmt)
    db.commit()


def get_latest_aquacrop_output(db: Session, farm_id: int) -> models.AquaCropOutput | None:
    return (
        db.query(models.AquaCropOutput)
        .filter(models.AquaCropOutput.farm_id == farm_id)
        .order_by(models.AquaCropOutput.as_of_date.desc())
        .first()
    )


def upsert_aquacrop_output(db: Session, farm_id: int, output: AquaCropOutputBase) -> models.AquaCropOutput:
    stmt = pg_insert(models.AquaCropOutput).values(farm_id=farm_id, **output.model_dump()).on_conflict_do_update(
        constraint="uq_aquacrop_farm_date",
        set_={**output.model_dump(exclude={"as_of_date"}), "run_date": func.now()},
    )
    db.execute(stmt)
    db.commit()
    return (
        db.query(models.AquaCropOutput)
        .filter(
            models.AquaCropOutput.farm_id == farm_id,
            models.AquaCropOutput.as_of_date == output.as_of_date,
        )
        .one()
    )


def create_baseline_irrigation(db: Session, farm_id: int, baseline: BaselineIrrigationCreate) -> models.BaselineIrrigation:
    db_baseline = models.BaselineIrrigation(**baseline.model_dump(), farm_id=farm_id)
    db.add(db_baseline)
    db.commit()
    db.refresh(db_baseline)
    return db_baseline


def get_baseline_irrigations_by_farm(
    db: Session,
    farm_id: int,
    skip: int = 0,
    limit: int = 10,
) -> list[models.BaselineIrrigation]:
    return (
        db.query(models.BaselineIrrigation)
        .filter(models.BaselineIrrigation.farm_id == farm_id)
        .order_by(models.BaselineIrrigation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_baseline_irrigations_by_farm(db: Session, farm_id: int) -> int:
    return (
        db.query(models.BaselineIrrigation)
        .filter(models.BaselineIrrigation.farm_id == farm_id)
        .count()
    )


def _water_savings_base_query(db: Session, farm_id: int, start_date: date | None, end_date: date | None) -> Query:
    query = db.query(models.WaterSavings).filter(models.WaterSavings.farm_id == farm_id)
    if start_date:
        query = query.filter(models.WaterSavings.period_end >= start_date)
    if end_date:
        query = query.filter(models.WaterSavings.period_start <= end_date)
    return query


def get_water_savings_by_farm(
    db: Session,
    farm_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[models.WaterSavings]:
    return (
        _water_savings_base_query(db, farm_id, start_date, end_date)
        .order_by(models.WaterSavings.period_start.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_water_savings_by_farm(
    db: Session,
    farm_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> int:
    return _water_savings_base_query(db, farm_id, start_date, end_date).count()


def get_active_farms(db: Session, today: date) -> list[models.Farm]:
    """Farms in season: planted, and not yet past harvest (no harvest date = still active)."""
    return (
        db.query(models.Farm)
        .filter(
            models.Farm.planting_date.isnot(None),
            models.Farm.planting_date <= today,
            or_(models.Farm.harvest_date.is_(None), models.Farm.harvest_date >= today),
        )
        .order_by(models.Farm.id)
        .all()
    )


def get_latest_et_date(db: Session, farm_id: int, source: str | None = None) -> date | None:
    """Latest cached reading date; pass source to consider only one provider
    (e.g. OpenET actuals, ignoring provisional CIMIS gap-fill rows)."""
    query = db.query(func.max(models.ETReading.reading_date)).filter(
        models.ETReading.farm_id == farm_id
    )
    if source is not None:
        query = query.filter(models.ETReading.source == source)
    return query.scalar()


def get_latest_baseline_irrigation(db: Session, farm_id: int) -> models.BaselineIrrigation | None:
    return (
        db.query(models.BaselineIrrigation)
        .filter(models.BaselineIrrigation.farm_id == farm_id)
        .order_by(models.BaselineIrrigation.created_at.desc())
        .first()
    )


def sum_irrigation_gallons(db: Session, farm_id: int, start_date: date, end_date: date) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(models.IrrigationEvent.gallons_applied), 0))
        .filter(
            models.IrrigationEvent.farm_id == farm_id,
            models.IrrigationEvent.event_date >= start_date,
            models.IrrigationEvent.event_date <= end_date,
        )
        .scalar()
    )
    return Decimal(total)


def upsert_water_savings(db: Session, farm_id: int, savings: WaterSavingsBase) -> models.WaterSavings:
    stmt = pg_insert(models.WaterSavings).values(farm_id=farm_id, **savings.model_dump()).on_conflict_do_update(
        constraint="uq_water_savings_farm_period",
        set_={
            **savings.model_dump(exclude={"period_start", "period_end"}),
            "computed_at": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()
    return (
        db.query(models.WaterSavings)
        .filter(
            models.WaterSavings.farm_id == farm_id,
            models.WaterSavings.period_start == savings.period_start,
            models.WaterSavings.period_end == savings.period_end,
        )
        .one()
    )


def get_water_savings_series(
    db: Session, farm_id: int, start_date: date, end_date: date
) -> list[models.WaterSavings]:
    return (
        db.query(models.WaterSavings)
        .filter(
            models.WaterSavings.farm_id == farm_id,
            models.WaterSavings.period_start >= start_date,
            models.WaterSavings.period_end <= end_date,
        )
        .order_by(models.WaterSavings.period_start)
        .all()
    )


def monthly_extraction_gallons(db: Session, farm_id: int, year: int) -> dict[int, Decimal]:
    """Month -> total gallons applied, from logged irrigation events."""
    rows = (
        db.query(
            func.extract("month", models.IrrigationEvent.event_date).label("month"),
            func.sum(models.IrrigationEvent.gallons_applied).label("gallons"),
        )
        .filter(
            models.IrrigationEvent.farm_id == farm_id,
            models.IrrigationEvent.event_date >= date(year, 1, 1),
            models.IrrigationEvent.event_date <= date(year, 12, 31),
        )
        .group_by("month")
        .all()
    )
    return {int(month): Decimal(gallons) for month, gallons in rows}


def count_farms_by_severity(db: Session) -> dict[str, int]:
    """Severity of each farm's LATEST AquaCropOutput, counted across all farms."""
    latest = (
        db.query(
            models.AquaCropOutput.farm_id,
            func.max(models.AquaCropOutput.as_of_date).label("max_date"),
        )
        .group_by(models.AquaCropOutput.farm_id)
        .subquery()
    )
    rows = (
        db.query(models.AquaCropOutput.severity, func.count())
        .join(
            latest,
            (models.AquaCropOutput.farm_id == latest.c.farm_id)
            & (models.AquaCropOutput.as_of_date == latest.c.max_date),
        )
        .group_by(models.AquaCropOutput.severity)
        .all()
    )
    counts = {"green": 0, "yellow": 0, "red": 0}
    for severity, count in rows:
        if severity is not None:
            counts[severity.value] = count
    return counts


def sum_all_water_savings(db: Session) -> tuple[Decimal, Decimal, Decimal]:
    row = db.query(
        func.coalesce(func.sum(models.WaterSavings.gallons_saved), 0),
        func.coalesce(func.sum(models.WaterSavings.kwh_saved), 0),
        func.coalesce(func.sum(models.WaterSavings.co2_kg_saved), 0),
    ).one()
    return Decimal(row[0]), Decimal(row[1]), Decimal(row[2])


def upsert_regional_stats(db: Session, snapshot_date: date, values: dict) -> models.RegionalStats:
    stmt = pg_insert(models.RegionalStats).values(snapshot_date=snapshot_date, **values).on_conflict_do_update(
        index_elements=["snapshot_date"],
        set_={**values, "computed_at": func.now()},
    )
    db.execute(stmt)
    db.commit()
    return (
        db.query(models.RegionalStats)
        .filter(models.RegionalStats.snapshot_date == snapshot_date)
        .one()
    )


def get_latest_regional_stats(db: Session) -> models.RegionalStats | None:
    return (
        db.query(models.RegionalStats)
        .order_by(models.RegionalStats.snapshot_date.desc())
        .first()
    )


def get_user_by_phone(db: Session, phone_number: str) -> models.User | None:
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()


def create_alert(
    db: Session,
    farm_id: int,
    severity: StressSeverity,
    as_of_date: date,
    days_to_stress: int | None,
    provider_message_sid: str | None,
) -> models.Alert:
    alert = models.Alert(
        farm_id=farm_id,
        severity=severity,
        as_of_date=as_of_date,
        days_to_stress=days_to_stress,
        provider_message_sid=provider_message_sid,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alert(db: Session, farm_id: int, as_of_date: date, severity: StressSeverity) -> models.Alert | None:
    return (
        db.query(models.Alert)
        .filter(
            models.Alert.farm_id == farm_id,
            models.Alert.as_of_date == as_of_date,
            models.Alert.severity == severity,
        )
        .first()
    )


def get_previous_severity(db: Session, farm_id: int, before_date: date) -> StressSeverity | None:
    """Severity of the newest sim output strictly before before_date — the
    baseline the alert dispatcher compares against for escalation."""
    row = (
        db.query(models.AquaCropOutput)
        .filter(
            models.AquaCropOutput.farm_id == farm_id,
            models.AquaCropOutput.as_of_date < before_date,
        )
        .order_by(models.AquaCropOutput.as_of_date.desc())
        .first()
    )
    return row.severity if row is not None else None


def get_latest_alert_for_user(db: Session, user_id: int, since: datetime | None = None) -> models.Alert | None:
    """Newest alert across all the user's farms — an SMS reply has no farm
    context, so it attaches to whatever was alerted most recently."""
    query = (
        db.query(models.Alert)
        .join(models.Farm, models.Alert.farm_id == models.Farm.id)
        .filter(models.Farm.user_id == user_id)
    )
    if since is not None:
        query = query.filter(models.Alert.sent_at >= since)
    return query.order_by(models.Alert.sent_at.desc(), models.Alert.id.desc()).first()


def set_alert_feedback(db: Session, alert: models.Alert, feedback: AlertFeedback) -> models.Alert:
    alert.feedback = feedback
    alert.feedback_at = func.now()
    db.commit()
    db.refresh(alert)
    return alert


def get_alerts_by_farm(db: Session, farm_id: int, skip: int = 0, limit: int = 10) -> list[models.Alert]:
    return (
        db.query(models.Alert)
        .filter(models.Alert.farm_id == farm_id)
        .order_by(models.Alert.sent_at.desc(), models.Alert.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_alerts_by_farm(db: Session, farm_id: int) -> int:
    return db.query(models.Alert).filter(models.Alert.farm_id == farm_id).count()


def create_job_run(db: Session, job_name: str) -> models.JobRun:
    job_run = models.JobRun(job_name=job_name, status=JobStatus.RUNNING)
    db.add(job_run)
    db.commit()
    db.refresh(job_run)
    return job_run


def finish_job_run(
    db: Session,
    job_run: models.JobRun,
    status: JobStatus,
    processed: int = 0,
    failed: int = 0,
    skipped: int = 0,
    detail: str | None = None,
) -> models.JobRun:
    job_run.status = status
    job_run.finished_at = func.now()
    job_run.farms_processed = processed
    job_run.farms_failed = failed
    job_run.farms_skipped = skipped
    job_run.detail = detail
    db.commit()
    db.refresh(job_run)
    return job_run


