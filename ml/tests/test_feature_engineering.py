import pytest
import numpy as np
import pandas as pd
from types import SimpleNamespace

from ml.feature_engineering import (
    normalize_crop_type,
    get_crop_context,
    compute_deficit,
    should_irrigate,
    build_feature_row,
    build_features_frame,
    build_features,
    prepare_training_frame,
    CROP_ENCODINGS,
    CROP_COEFFICIENTS,
    DEFAULT_CROP_TYPE,
    IRRIGATION_DEFICIT_THRESHOLD_MM,
    FEATURE_COLUMNS,
)


# ── helpers ──────────────────────────────────────────────────────────────────


def make_weather(**kwargs):
    defaults = dict(
        temperature_c=25.0,
        humidity_pct=60.0,
        wind_speed_kph=10.0,
        rainfall_mm=1.0,
        et0_mm=4.5,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_farm_ml(**kwargs):
    defaults = dict(crop_type="almonds")
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_raw_df(n=5, et0=5.0, rain=0.0):
    return pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=n).astype(str),
        "Avg Air Temp (C)": [25.0] * n,
        "Avg Rel Hum (%)": [60.0] * n,
        "Avg Wind Speed (m/s)": [2.0] * n,
        "Precip (mm)": [rain] * n,
        "ETo (mm)": [et0] * n,
    })


# ── normalize_crop_type ──────────────────────────────────────────────────────


def test_normalize_known_crop_almonds():
    assert normalize_crop_type("almonds") == "almonds"


def test_normalize_known_crop_grapes():
    assert normalize_crop_type("grapes") == "grapes"


def test_normalize_unknown_crop_returns_default():
    assert normalize_crop_type("banana") == DEFAULT_CROP_TYPE


def test_normalize_none_returns_default():
    assert normalize_crop_type(None) == DEFAULT_CROP_TYPE


def test_normalize_empty_string_returns_default():
    assert normalize_crop_type("") == DEFAULT_CROP_TYPE


def test_normalize_strips_whitespace_and_lowercases():
    assert normalize_crop_type("  ALMONDS  ") == "almonds"
    assert normalize_crop_type("GRAPES") == "grapes"


# ── get_crop_context ──────────────────────────────────────────────────────────


def test_get_crop_context_almonds():
    enc, kc = get_crop_context("almonds")
    assert enc == CROP_ENCODINGS["almonds"]
    assert kc == CROP_COEFFICIENTS["almonds"]


def test_get_crop_context_grapes():
    enc, kc = get_crop_context("grapes")
    assert enc == CROP_ENCODINGS["grapes"]
    assert kc == CROP_COEFFICIENTS["grapes"]


def test_get_crop_context_unknown_falls_back_to_default():
    enc, kc = get_crop_context("unknown_crop")
    default_enc, default_kc = get_crop_context(DEFAULT_CROP_TYPE)
    assert enc == default_enc
    assert kc == default_kc


def test_get_crop_context_returns_two_values():
    result = get_crop_context("almonds")
    assert len(result) == 2


# ── compute_deficit ───────────────────────────────────────────────────────────


def test_compute_deficit_basic():
    # deficit = (et0 * kc) - rainfall = (5 * 1.15) - 2 = 3.75
    assert compute_deficit(5.0, 2.0, 1.15) == pytest.approx(3.75)


def test_compute_deficit_zero_rainfall():
    assert compute_deficit(4.0, 0.0, 1.0) == pytest.approx(4.0)


def test_compute_deficit_negative_when_rain_exceeds_et():
    assert compute_deficit(2.0, 10.0, 1.0) == pytest.approx(-8.0)


def test_compute_deficit_with_pandas_series():
    et0 = pd.Series([4.0, 6.0])
    rain = pd.Series([1.0, 2.0])
    result = compute_deficit(et0, rain, 1.0)
    pd.testing.assert_series_equal(result, pd.Series([3.0, 4.0]))


# ── should_irrigate ───────────────────────────────────────────────────────────


def test_should_irrigate_above_threshold_returns_one():
    assert should_irrigate(IRRIGATION_DEFICIT_THRESHOLD_MM + 0.1) == 1


def test_should_irrigate_below_threshold_returns_zero():
    assert should_irrigate(IRRIGATION_DEFICIT_THRESHOLD_MM - 0.1) == 0


def test_should_irrigate_exactly_at_threshold_returns_zero():
    # condition is >, not >=
    assert should_irrigate(IRRIGATION_DEFICIT_THRESHOLD_MM) == 0


def test_should_irrigate_with_pandas_series():
    s = pd.Series([0.5, IRRIGATION_DEFICIT_THRESHOLD_MM + 0.1, 5.0])
    result = should_irrigate(s)
    assert list(result) == [0, 1, 1]


# ── build_feature_row ─────────────────────────────────────────────────────────


def test_build_feature_row_contains_all_feature_columns():
    row = build_feature_row(make_weather(), make_farm_ml())
    assert set(row.keys()) == set(FEATURE_COLUMNS)


def test_build_feature_row_wind_converted_from_kph_to_mps():
    row = build_feature_row(make_weather(wind_speed_kph=36.0), make_farm_ml())
    assert row["wind_speed_mps"] == pytest.approx(10.0)


def test_build_feature_row_none_values_default_to_zero():
    weather = SimpleNamespace(
        temperature_c=None, humidity_pct=None,
        wind_speed_kph=None, rainfall_mm=None, et0_mm=None,
    )
    row = build_feature_row(weather, make_farm_ml())
    assert row["temperature_c"] == 0.0
    assert row["rainfall_mm"] == 0.0
    assert row["et0_mm"] == 0.0


def test_build_feature_row_crop_context_almonds():
    row = build_feature_row(make_weather(), make_farm_ml(crop_type="almonds"))
    assert row["crop_encoded"] == float(CROP_ENCODINGS["almonds"])
    assert row["kc"] == CROP_COEFFICIENTS["almonds"]


def test_build_feature_row_crop_context_grapes():
    row = build_feature_row(make_weather(), make_farm_ml(crop_type="grapes"))
    assert row["crop_encoded"] == float(CROP_ENCODINGS["grapes"])
    assert row["kc"] == CROP_COEFFICIENTS["grapes"]


# ── build_features_frame ──────────────────────────────────────────────────────


def test_build_features_frame_shape():
    frame = build_features_frame(make_weather(), make_farm_ml())
    assert frame.shape == (1, len(FEATURE_COLUMNS))


def test_build_features_frame_column_order():
    frame = build_features_frame(make_weather(), make_farm_ml())
    assert list(frame.columns) == FEATURE_COLUMNS


# ── build_features ────────────────────────────────────────────────────────────


def test_build_features_returns_numpy_array():
    arr = build_features(make_weather(), make_farm_ml())
    assert isinstance(arr, np.ndarray)


def test_build_features_shape():
    arr = build_features(make_weather(), make_farm_ml())
    assert arr.shape == (1, len(FEATURE_COLUMNS))


# ── prepare_training_frame ────────────────────────────────────────────────────


def test_prepare_training_frame_output_columns():
    expected = ["Date", *FEATURE_COLUMNS, "deficit_mm", "irrigate"]
    df = prepare_training_frame(make_raw_df())
    assert list(df.columns) == expected


def test_prepare_training_frame_row_count_preserved():
    df = prepare_training_frame(make_raw_df(10))
    assert len(df) == 10


def test_prepare_training_frame_drops_qc_columns():
    raw = make_raw_df()
    raw["qc"] = 1
    raw["qc.temp"] = 1
    df = prepare_training_frame(raw)
    assert "qc" not in df.columns
    assert "qc.temp" not in df.columns


def test_prepare_training_frame_drops_station_columns():
    raw = make_raw_df()
    raw["Stn Id"] = "123"
    raw["Stn Name"] = "Station"
    raw["CIMIS Region"] = "Region"
    df = prepare_training_frame(raw)
    assert "Stn Id" not in df.columns
    assert "Stn Name" not in df.columns
    assert "CIMIS Region" not in df.columns


def test_prepare_training_frame_drops_rows_with_nan_in_et0():
    raw = make_raw_df(5)
    raw.loc[2, "ETo (mm)"] = None
    df = prepare_training_frame(raw)
    assert len(df) == 4


def test_prepare_training_frame_drops_rows_with_nan_in_temp():
    raw = make_raw_df(5)
    raw.loc[0, "Avg Air Temp (C)"] = None
    df = prepare_training_frame(raw)
    assert len(df) == 4


def test_prepare_training_frame_irrigate_one_when_deficit_exceeds_threshold():
    # almonds kc=1.15, et0=5, rain=0 → deficit=5.75 > 1.5 → irrigate=1
    df = prepare_training_frame(make_raw_df(n=3, et0=5.0, rain=0.0), crop_type="almonds")
    assert (df["irrigate"] == 1).all()


def test_prepare_training_frame_irrigate_zero_when_rain_covers_et():
    # et0=1, rain=10 → deficit < 0 < threshold → irrigate=0
    df = prepare_training_frame(make_raw_df(n=3, et0=1.0, rain=10.0))
    assert (df["irrigate"] == 0).all()


def test_prepare_training_frame_sorted_by_date():
    raw = make_raw_df(5)
    raw["Date"] = ["2025-01-05", "2025-01-01", "2025-01-03", "2025-01-02", "2025-01-04"]
    df = prepare_training_frame(raw)
    dates = df["Date"].tolist()
    assert dates == sorted(dates)


def test_prepare_training_frame_renames_source_columns():
    df = prepare_training_frame(make_raw_df())
    assert "Avg Air Temp (C)" not in df.columns
    assert "temperature_c" in df.columns
    assert "ETo (mm)" not in df.columns
    assert "et0_mm" in df.columns
