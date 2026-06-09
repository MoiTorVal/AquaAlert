from backend import models
from backend.schemas import (
    FarmCreate, FarmUpdate, WeatherReadingCreate, IrrigationEventCreate, BaselineIrrigationCreate,
    ETReadingCreate, AquaCropOutputBase, WaterSavingsBase,
)
from backend.enums import IrrigationSource, JobStatus
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

def get_weather_reading(db: Session, weather_reading_id: int) -> models.WeatherReading | None:
    return db.query(models.WeatherReading).filter(models.WeatherReading.id == weather_reading_id).first()

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


def create_irrigation_event(db: Session, farm_id: int, event: IrrigationEventCreate) -> models.IrrigationEvent:
    db_event = models.IrrigationEvent(
        **event.model_dump(),
        farm_id=farm_id,
        source=IrrigationSource.USER_LOG,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


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


def get_latest_et_date(db: Session, farm_id: int) -> date | None:
    return (
        db.query(func.max(models.ETReading.reading_date))
        .filter(models.ETReading.farm_id == farm_id)
        .scalar()
    )


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


