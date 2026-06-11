import logging

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from backend import crud
from backend.schemas import (
    FarmCreate, FarmUpdate, FarmResponse,
    WeatherReadingResponse, PaginatedWeatherResponse,
    IrrigationEventCreate, IrrigationEventResponse, PaginatedIrrigationEventResponse,
    BaselineIrrigationCreate, BaselineIrrigationResponse, PaginatedBaselineIrrigationResponse,
    AlertResponse, PaginatedAlertResponse,
    WaterSavingsResponse, PaginatedWaterSavingsResponse,
    SavingsSeriesResponse, SavingsTotals,
    ETReadingCreate, ETReadingResponse, ETSeriesResponse,
    AquaCropOutputRead, WaterStressResponse,
)
from datetime import datetime, date, timedelta
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User
from backend.services import openet_client, sgma_export
from backend.services import scheduler as scheduler_service
from backend.services.openet_client import ET_SOURCE, OpenETError, OpenETRateLimitError

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_ET_RANGE_DAYS = 366


def _validate_farm_ownership(db: Session, farm_id: int, user_id: int):
    db_farm = crud.get_farm(db=db, farm_id=farm_id)
    if db_farm is None or db_farm.user_id != user_id:
        raise HTTPException(status_code=404, detail="Farm not found")
    return db_farm

@router.post("/", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_farm(db=db, farm=farm, user_id=current_user.id)

@router.get("/{farm_id}", response_model=FarmResponse)
def read_farm(farm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    return db_farm

@router.get("/", response_model=list[FarmResponse])
def read_farms(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_farms(db=db, user_id=current_user.id, skip=skip, limit=limit)

@router.delete("/{farm_id}", response_model=FarmResponse)
def delete_farm(farm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    return crud.delete_farm(db=db, farm=db_farm)

@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, farm_update: FarmUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    return crud.update_farm(db=db, farm=db_farm, farm_update=farm_update)


@router.get("/{farm_id}/weather", response_model=PaginatedWeatherResponse)
def read_weather_readings_by_farm(
    farm_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    
    results = crud.get_weather_readings_by_farm(
        db=db, farm_id=farm_id, skip=skip, limit=limit,
        start_date=start_date, end_date=end_date,
    )
    total = crud.count_weather_readings_by_farm(
        db=db, farm_id=farm_id, start_date=start_date, end_date=end_date,
    )

    return PaginatedWeatherResponse(total=total, skip=skip, limit=limit, results=[WeatherReadingResponse.model_validate(r) for r in results])


@router.post(
    "/{farm_id}/irrigation-events",
    response_model=IrrigationEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def log_irrigation_event(
    farm_id: int,
    event: IrrigationEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    return crud.create_irrigation_event(db=db, farm_id=farm_id, event=event)


@router.get("/{farm_id}/irrigation-events", response_model=PaginatedIrrigationEventResponse)
def list_irrigation_events(
    farm_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    results = crud.get_irrigation_events_by_farm(
        db=db, farm_id=farm_id, skip=skip, limit=limit,
        start_date=start_date, end_date=end_date,
    )
    total = crud.count_irrigation_events_by_farm(
        db=db, farm_id=farm_id, start_date=start_date, end_date=end_date,
    )
    return PaginatedIrrigationEventResponse(
        total=total, skip=skip, limit=limit,
        results=[IrrigationEventResponse.model_validate(r) for r in results],
    )


@router.get("/{farm_id}/alerts", response_model=PaginatedAlertResponse)
def list_alerts(
    farm_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    results = crud.get_alerts_by_farm(db=db, farm_id=farm_id, skip=skip, limit=limit)
    total = crud.count_alerts_by_farm(db=db, farm_id=farm_id)
    return PaginatedAlertResponse(
        total=total, skip=skip, limit=limit,
        results=[AlertResponse.model_validate(r) for r in results],
    )


@router.get("/{farm_id}/water-stress", response_model=WaterStressResponse)
def get_water_stress(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Latest cached AquaCrop result; sims never run on the request path (scheduler computes them)."""
    _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    output = crud.get_latest_aquacrop_output(db=db, farm_id=farm_id)
    if output is None:
        raise HTTPException(status_code=404, detail="No water-stress data available yet for this farm")
    et_latest_date = crud.get_latest_et_date(db=db, farm_id=farm_id)
    return WaterStressResponse(
        **AquaCropOutputRead.model_validate(output).model_dump(),
        et_latest_date=et_latest_date,
        et_latest_actual_date=crud.get_latest_et_date(db=db, farm_id=farm_id, source=ET_SOURCE),
        et_is_stale=scheduler_service.is_et_stale(et_latest_date),
    )


@router.get("/{farm_id}/et", response_model=ETSeriesResponse)
async def get_et_series(
    farm_id: int,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    if to_date < from_date:
        raise HTTPException(status_code=422, detail="'to' must be on or after 'from'")
    if (to_date - from_date).days + 1 > MAX_ET_RANGE_DAYS:
        raise HTTPException(status_code=422, detail=f"Date range cannot exceed {MAX_ET_RANGE_DAYS} days")
    if db_farm.field_polygon is None:
        raise HTTPException(status_code=400, detail="Farm has no field polygon; draw the field boundary first")

    cached = crud.get_et_readings_by_farm(db=db, farm_id=farm_id, start_date=from_date, end_date=to_date)
    cached_dates = {r.reading_date for r in cached}
    today = date.today()
    requested = [from_date + timedelta(days=i) for i in range((to_date - from_date).days + 1)]
    missing = [d for d in requested if d not in cached_dates and d <= today]

    if missing:
        geometry = openet_client.polygon_to_geometry(to_shape(db_farm.field_polygon))
        try:
            points = await openet_client.fetch_daily_et(geometry, missing[0], missing[-1])
        except OpenETRateLimitError as exc:
            logger.warning("OpenET rate limit for farm %d: %s", farm_id, exc)
            raise HTTPException(status_code=503, detail="ET data provider rate limit reached; try again later")
        except OpenETError as exc:
            logger.error("OpenET fetch failed for farm %d: %s", farm_id, exc)
            raise HTTPException(status_code=502, detail="ET data provider is unavailable")

        points = openet_client.trim_gapfill_tail(points)
        missing_set = set(missing)
        new_readings = [
            ETReadingCreate(
                farm_id=farm_id,
                reading_date=p["reading_date"],
                et_mm=p["et_mm"],
                source=ET_SOURCE,
            )
            for p in points
            if p["reading_date"] in missing_set
        ]
        if new_readings:
            crud.create_et_readings(db=db, readings=new_readings)
            cached = crud.get_et_readings_by_farm(db=db, farm_id=farm_id, start_date=from_date, end_date=to_date)

    as_of = max((r.reading_date for r in cached), default=None)
    return ETSeriesResponse(
        farm_id=farm_id,
        start_date=from_date,
        end_date=to_date,
        as_of=as_of,
        results=[ETReadingResponse.model_validate(r) for r in cached],
    )


@router.post(
    "/{farm_id}/baseline-irrigations",
    response_model=BaselineIrrigationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_baseline_irrigation(
    farm_id: int,
    baseline: BaselineIrrigationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    return crud.create_baseline_irrigation(db=db, farm_id=farm_id, baseline=baseline)


@router.get("/{farm_id}/baseline-irrigations", response_model=PaginatedBaselineIrrigationResponse)
def list_baseline_irrigations(
    farm_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    results = crud.get_baseline_irrigations_by_farm(db=db, farm_id=farm_id, skip=skip, limit=limit)
    total = crud.count_baseline_irrigations_by_farm(db=db, farm_id=farm_id)
    return PaginatedBaselineIrrigationResponse(
        total=total, skip=skip, limit=limit,
        results=[BaselineIrrigationResponse.model_validate(r) for r in results],
    )


@router.get("/{farm_id}/savings", response_model=SavingsSeriesResponse)
def get_savings_series(
    farm_id: int,
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    if to_date < from_date:
        raise HTTPException(status_code=422, detail="'to' must be on or after 'from'")
    rows = crud.get_water_savings_series(db=db, farm_id=farm_id, start_date=from_date, end_date=to_date)
    totals = SavingsTotals(
        baseline_gallons=sum((r.baseline_gallons for r in rows), Decimal("0")),
        actual_gallons=sum((r.actual_gallons for r in rows), Decimal("0")),
        gallons_saved=sum((r.gallons_saved for r in rows), Decimal("0")),
        kwh_saved=sum((r.kwh_saved for r in rows), Decimal("0")),
        co2_kg_saved=sum((r.co2_kg_saved for r in rows), Decimal("0")),
    )
    return SavingsSeriesResponse(
        farm_id=farm_id, start_date=from_date, end_date=to_date, totals=totals,
        results=[WaterSavingsResponse.model_validate(r) for r in rows],
    )


@router.get("/{farm_id}/sgma-export")
def sgma_export_report(
    farm_id: int,
    year: int = Query(ge=2020, le=2100),
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_farm = _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    monthly = crud.monthly_extraction_gallons(db=db, farm_id=farm_id, year=year)
    source_counts = crud.extraction_source_counts(db=db, farm_id=farm_id, year=year)
    filename = f"sgma-report-{year}-farm-{farm_id}.{format}"
    if format == "pdf":
        content: bytes | str = sgma_export.build_pdf(
            db_farm, year, monthly, owner=current_user, source_counts=source_counts
        )
        media_type = "application/pdf"
    else:
        content = sgma_export.build_csv(
            db_farm, year, monthly, owner=current_user, source_counts=source_counts
        )
        media_type = "text/csv"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{farm_id}/water-savings", response_model=PaginatedWaterSavingsResponse)
def list_water_savings(
    farm_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_farm_ownership(db=db, farm_id=farm_id, user_id=current_user.id)
    results = crud.get_water_savings_by_farm(
        db=db, farm_id=farm_id, skip=skip, limit=limit,
        start_date=start_date, end_date=end_date,
    )
    total = crud.count_water_savings_by_farm(
        db=db, farm_id=farm_id, start_date=start_date, end_date=end_date,
    )
    return PaginatedWaterSavingsResponse(
        total=total, skip=skip, limit=limit,
        results=[WaterSavingsResponse.model_validate(r) for r in results],
    )

