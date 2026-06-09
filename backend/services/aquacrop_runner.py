"""AquaCrop-OSPy wrapper: pure simulation core, DB I/O at the edges.

run_simulation() is deterministic and touches no I/O; compute_and_cache_water_stress()
is the DB edge used by the Phase 6 scheduler. Route handlers only read the cache.

Modeling simplifications (documented for Phase 9 ML residual correction):
- OpenET actual ET is fed to AquaCrop as ReferenceET.
- Fixed growing-season temperatures (CA Central Valley climatology) and zero
  precipitation (irrigated summer fields); rainfall integration is future work.
"""
import logging
from datetime import date

import pandas as pd
from aquacrop import AquaCropModel, Crop, InitialWaterContent, Soil
from sqlalchemy.orm import Session

from backend import crud, models
from backend.enums import SoilTexture, StressSeverity
from backend.schemas import AquaCropOutputBase

logger = logging.getLogger(__name__)

SIM_TMIN_C = 12.0
SIM_TMAX_C = 30.0
# Dr >= RAW (p_up[1] * TAW, stomatal closure) is red; yellow warns at this fraction of RAW.
WARNING_FRACTION = 0.8
# trailing days used to estimate the current depletion rate
RATE_WINDOW_DAYS = 7

CROP_TYPE_TO_AQUACROP = {
    "alfalfa": "AlfalfaGDD",
    "barley": "Barley",
    "cassava": "Cassava",
    "corn": "Maize",
    "cotton": "Cotton",
    "drybean": "DryBean",
    "maize": "Maize",
    "potato": "Potato",
    "quinoa": "Quinoa",
    "rice": "PaddyRice",
    "sorghum": "Sorghum",
    "soybean": "Soybean",
    "sugarbeet": "SugarBeet",
    "sunflower": "Sunflower",
    "tomato": "Tomato",
    "wheat": "Wheat",
}

SOIL_TEXTURE_TO_AQUACROP = {
    SoilTexture.Sandy: "Sand",
    SoilTexture.LoamySand: "LoamySand",
    SoilTexture.SandyLoam: "SandyLoam",
    SoilTexture.Loam: "Loam",
    SoilTexture.SiltLoam: "SiltLoam",
    SoilTexture.Silt: "Silt",
    SoilTexture.SandyClayLoam: "SandyClayLoam",
    SoilTexture.ClayLoam: "ClayLoam",
    SoilTexture.SiltyClayLoam: "SiltClayLoam",
    SoilTexture.SandyClay: "SandyClay",
    SoilTexture.SiltyClay: "SiltClay",
    SoilTexture.Clay: "Clay",
}


class AquaCropInputError(ValueError):
    """Farm or series data is unusable for simulation."""


def map_crop_type(crop_type: str | None) -> str:
    if crop_type is None:
        raise AquaCropInputError("Farm has no crop_type set")
    try:
        return CROP_TYPE_TO_AQUACROP[crop_type.strip().lower()]
    except KeyError:
        raise AquaCropInputError(
            f"Unsupported crop type {crop_type!r}; supported: {sorted(CROP_TYPE_TO_AQUACROP)}"
        ) from None


def map_soil_texture(soil_texture: SoilTexture | None) -> str:
    if soil_texture is None:
        raise AquaCropInputError("Farm has no soil_type set")
    return SOIL_TEXTURE_TO_AQUACROP[soil_texture]


def classify_severity(depletion_mm: float, raw_threshold_mm: float) -> StressSeverity:
    if depletion_mm >= raw_threshold_mm:
        return StressSeverity.RED
    if depletion_mm >= WARNING_FRACTION * raw_threshold_mm:
        return StressSeverity.YELLOW
    return StressSeverity.GREEN


def project_days_to_stress(depletion_series_mm: list[float], raw_threshold_mm: float) -> int | None:
    """Linear projection: days until depletion crosses RAW at the recent rate.

    Returns 0 when already at/past the threshold, None when depletion is flat
    or falling (not approaching stress at the current rate).
    """
    current = depletion_series_mm[-1]
    if current >= raw_threshold_mm:
        return 0
    window = depletion_series_mm[-(RATE_WINDOW_DAYS + 1):]
    if len(window) < 2:
        return None
    rate = (window[-1] - window[0]) / (len(window) - 1)
    if rate <= 0:
        return None
    days = (raw_threshold_mm - current) / rate
    return max(1, round(days))


def _build_weather_df(et_series: list[tuple[date, float]]) -> pd.DataFrame:
    dates = pd.DatetimeIndex([pd.Timestamp(d) for d, _ in et_series])
    df = pd.DataFrame(
        {
            "MinTemp": SIM_TMIN_C,
            "MaxTemp": SIM_TMAX_C,
            "Precipitation": 0.0,
            "ReferenceET": [et for _, et in et_series],
        },
        index=dates,
    )
    # AquaCrop needs a continuous daily series; forward-fill small gaps.
    df = df.asfreq("D").ffill()
    df["Date"] = df.index
    return df.reset_index(drop=True)


def run_simulation(
    et_series: list[tuple[date, float]],
    crop_type: str | None,
    soil_texture: SoilTexture | None,
    planting_date: date | None,
) -> AquaCropOutputBase:
    """Run AquaCrop from the start of the ET series and return field state on the last day."""
    crop_name = map_crop_type(crop_type)
    soil_name = map_soil_texture(soil_texture)
    if planting_date is None:
        raise AquaCropInputError("Farm has no planting_date set")
    if not et_series:
        raise AquaCropInputError("ET series is empty")

    et_series = sorted(et_series)
    start, end = et_series[0][0], et_series[-1][0]
    if planting_date < start:
        raise AquaCropInputError(
            f"ET series must start on or before planting_date ({planting_date}); starts {start}"
        )
    if planting_date > end:
        raise AquaCropInputError(f"planting_date ({planting_date}) is after the ET series end ({end})")

    model = AquaCropModel(
        sim_start_time=start.strftime("%Y/%m/%d"),
        sim_end_time=end.strftime("%Y/%m/%d"),
        weather_df=_build_weather_df(et_series),
        soil=Soil(soil_name),
        crop=Crop(crop_name, planting_date=planting_date.strftime("%m/%d")),
        initial_water_content=InitialWaterContent(value=["FC"]),
    )

    # step daily to record the depletion trajectory for days_to_stress;
    # initialize_model=False is required — the default re-initializes (resets
    # the sim to day 0) on every run_model call, which never terminates
    model._initialize()
    depletion_series: list[float] = []
    taw = 0.0
    while not model._clock_struct.model_is_finished:
        model.run_model(num_steps=1, initialize_model=False)
        depletion_series.append(float(model._init_cond.depletion))
        taw = float(model._init_cond.taw)

    if taw <= 0:
        raise AquaCropInputError("Simulation produced no root-zone water capacity (TAW = 0)")

    depletion = depletion_series[-1]
    raw_threshold = float(model.crop.p_up[1]) * taw
    return AquaCropOutputBase(
        as_of_date=end,
        depletion_mm=round(depletion, 2),
        paw_mm=round(taw - depletion, 2),
        raw_threshold_mm=round(raw_threshold, 2),
        root_zone_moisture_pct=round((taw - depletion) / taw * 100, 2),
        severity=classify_severity(depletion, raw_threshold),
        days_to_stress=project_days_to_stress(depletion_series, raw_threshold),
    )


def compute_and_cache_water_stress(db: Session, farm: models.Farm, as_of_date: date) -> models.AquaCropOutput:
    """DB edge: load the farm's cached ET series, simulate, upsert AquaCropOutput."""
    readings = crud.get_et_readings_by_farm(
        db=db, farm_id=farm.id, start_date=farm.planting_date, end_date=as_of_date
    )
    et_series = [(r.reading_date, float(r.et_mm)) for r in readings]
    result = run_simulation(
        et_series=et_series,
        crop_type=farm.crop_type,
        soil_texture=farm.soil_type,
        planting_date=farm.planting_date,
    )
    return crud.upsert_aquacrop_output(db=db, farm_id=farm.id, output=result)
