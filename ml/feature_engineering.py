from __future__ import annotations
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd



if TYPE_CHECKING:
    from backend.models import Farm, WeatherReading
else:
    Farm = Any
    WeatherReading = Any


CROP_ENCODINGS = {
    "almonds": 0,
    "grapes": 1,
}

CROP_COEFFICIENTS = {
    "almonds": 1.15,
    "grapes": 0.85,
}

DEFAULT_CROP_TYPE = "almonds"
IRRIGATION_DEFICIT_THRESHOLD_MM = 1.5

FEATURE_COLUMNS = [
    "temperature_c",
    "humidity_pct",
    "wind_speed_mps",
    "rainfall_mm",
    "et0_mm",
    "kc",
    "crop_encoded",
]

TRAINING_COLUMN_MAP = {
    "Avg Air Temp (C)": "temperature_c",
    "Avg Rel Hum (%)": "humidity_pct",
    "Avg Wind Speed (m/s)": "wind_speed_mps",
    "Precip (mm)": "rainfall_mm",
    "ETo (mm)": "et0_mm",
}


def normalize_crop_type(crop_type: str | None) -> str:
    normalized = (crop_type or DEFAULT_CROP_TYPE).strip().lower()
    return normalized if normalized in CROP_ENCODINGS else DEFAULT_CROP_TYPE


def get_crop_context(crop_type: str | None) -> tuple[int, float]:
    normalized_crop_type = normalize_crop_type(crop_type)
    return (
        CROP_ENCODINGS[normalized_crop_type],
        CROP_COEFFICIENTS[normalized_crop_type],
    )


def compute_deficit(et0_mm: Any, rainfall_mm: Any, kc: Any) -> Any:
    return (et0_mm * kc) - rainfall_mm


def should_irrigate(deficit_mm: Any) -> Any:
    irrigation_needed = deficit_mm > IRRIGATION_DEFICIT_THRESHOLD_MM
    if hasattr(irrigation_needed, "astype"):
        return irrigation_needed.astype(int)
    return int(irrigation_needed)


def build_feature_row(weather: WeatherReading, farm: Farm) -> dict[str, float]:
    crop_encoded, kc = get_crop_context(farm.crop_type)

    return {
        "temperature_c": float(weather.temperature_c or 0),
        "humidity_pct": float(weather.humidity_pct or 0),
        "wind_speed_mps": float(weather.wind_speed_kph or 0) / 3.6,
        "rainfall_mm": float(weather.rainfall_mm or 0),
        "et0_mm": float(weather.et0_mm or 0),
        "kc": kc,
        "crop_encoded": float(crop_encoded),
    }


def build_features_frame(weather: WeatherReading, farm: Farm) -> pd.DataFrame:
    return pd.DataFrame([build_feature_row(weather, farm)], columns=FEATURE_COLUMNS)


def build_features(weather: WeatherReading, farm: Farm) -> np.ndarray:
    return build_features_frame(weather, farm).to_numpy()


def prepare_training_frame(raw_df: pd.DataFrame, crop_type: str = DEFAULT_CROP_TYPE) -> pd.DataFrame:
    df = raw_df.copy()

    df["Date"] = pd.to_datetime(df["Date"])

    for source_column in TRAINING_COLUMN_MAP:
        df[source_column] = pd.to_numeric(df[source_column], errors="coerce")

    qc_columns = [column for column in df.columns if column == "qc" or column.startswith("qc.")]
    drop_columns = qc_columns + ["Stn Id", "Stn Name", "CIMIS Region", "Jul"]
    existing_drop_columns = [column for column in drop_columns if column in df.columns]
    df = df.drop(columns=existing_drop_columns)
    df = df.dropna(subset=["Date", *TRAINING_COLUMN_MAP.keys()]).copy()

    df = df.rename(columns=TRAINING_COLUMN_MAP)

    crop_encoded, kc = get_crop_context(crop_type)
    df["kc"] = kc
    df["crop_encoded"] = float(crop_encoded)
    df["deficit_mm"] = compute_deficit(df["et0_mm"], df["rainfall_mm"], df["kc"])
    df["irrigate"] = should_irrigate(df["deficit_mm"])

    return df[["Date", *FEATURE_COLUMNS, "deficit_mm", "irrigate"]].sort_values("Date").reset_index(drop=True)
