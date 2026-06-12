from datetime import date

import numpy as np
import pytest
from shapely.geometry import Polygon

from backend.services import sentinel_client
from backend.services.sentinel_client import (
    SentinelRequestError,
    SentinelUnavailableError,
    fetch_latest_ndvi,
)

POLYGON = Polygon(
    [(-120.1, 36.9), (-120.1, 36.91), (-120.09, 36.91), (-120.09, 36.9)]
)
BOUNDS = (36.9, -120.1, 36.91, -120.09)  # (south, west, north, east)


class _Asset:
    def __init__(self, href: str):
        self.href = href


class _Item:
    def __init__(self, dt: str, cloud: float | None):
        self.properties = {"datetime": dt, "eo:cloud_cover": cloud}
        self.assets = {"B04": _Asset("red.tif"), "B08": _Asset("nir.tif")}


def test_fetch_latest_ndvi_selects_most_recent_scene_under_cloud_limit(monkeypatch):
    items = [
        _Item("2026-06-10T10:00:00Z", 42.0),
        _Item("2026-06-09T10:00:00Z", 9.5),
    ]
    monkeypatch.setattr(sentinel_client, "_search_items", lambda *args, **kwargs: items)
    monkeypatch.setattr(
        sentinel_client,
        "_read_clipped_band",
        lambda *args, **kwargs: (
            np.array([[0.2, 0.3]], dtype="float32"),
            np.array([[True, True]]),
            BOUNDS,
        ),
    )
    result = fetch_latest_ndvi(POLYGON, max_cloud_pct=15, lookback_days=14)
    assert result["scan_date"] == date(2026, 6, 9)
    assert result["cloud_cover_pct"] == 9.5
    assert result["ndvi_grid_bounds"] == [[36.9, -120.1], [36.91, -120.09]]


def test_fetch_latest_ndvi_cloud_filter_no_scene(monkeypatch):
    monkeypatch.setattr(
        sentinel_client,
        "_search_items",
        lambda *args, **kwargs: [_Item("2026-06-10T10:00:00Z", 35.0)],
    )
    with pytest.raises(SentinelUnavailableError, match="No acceptable Sentinel-2 scene"):
        fetch_latest_ndvi(POLYGON, max_cloud_pct=15)


def test_fetch_latest_ndvi_no_scene_in_window(monkeypatch):
    monkeypatch.setattr(sentinel_client, "_search_items", lambda *args, **kwargs: [])
    with pytest.raises(SentinelUnavailableError, match="No acceptable Sentinel-2 scene"):
        fetch_latest_ndvi(POLYGON)


def test_fetch_latest_ndvi_ndvi_math_and_boundary_mask(monkeypatch):
    monkeypatch.setattr(
        sentinel_client,
        "_search_items",
        lambda *args, **kwargs: [_Item("2026-06-08T10:00:00Z", 6.2)],
    )
    red = np.array([[0.2, 0.3], [0.4, 0.1]], dtype="float32")
    nir = np.array([[0.6, 0.5], [0.8, 0.4]], dtype="float32")
    inside = np.array([[True, False], [True, True]])

    def fake_read(href, polygon_geojson):
        if "red" in href:
            return red.copy(), inside.copy(), BOUNDS
        return nir.copy(), inside.copy(), BOUNDS

    monkeypatch.setattr(sentinel_client, "_read_clipped_band", fake_read)
    result = fetch_latest_ndvi(POLYGON)

    assert result["ndvi_grid"] == [[0.5, None], [0.333, 0.6]]
    assert result["mean_ndvi"] == pytest.approx(0.478, abs=1e-6)
    assert result["max_ndvi"] == pytest.approx(0.6, abs=1e-6)
    assert result["min_ndvi"] == pytest.approx(0.333, abs=1e-6)


def test_fetch_latest_ndvi_raises_for_misaligned_assets(monkeypatch):
    monkeypatch.setattr(
        sentinel_client,
        "_search_items",
        lambda *args, **kwargs: [_Item("2026-06-08T10:00:00Z", 6.2)],
    )

    def fake_read(href, polygon_geojson):
        if "red" in href:
            return np.ones((2, 2), dtype="float32"), np.ones((2, 2), dtype=bool), BOUNDS
        return np.ones((1, 2), dtype="float32"), np.ones((1, 2), dtype=bool), BOUNDS

    monkeypatch.setattr(sentinel_client, "_read_clipped_band", fake_read)
    with pytest.raises(SentinelRequestError, match="misaligned"):
        fetch_latest_ndvi(POLYGON)


# ── _read_clipped_band against a real (tiny) GeoTIFF ─────────────────────────


def _write_test_band(path, data, *, nodata=0, scales=None, offsets=None):
    import rasterio
    from rasterio.transform import from_origin

    # 4x4 pixels of 0.0025 deg exactly covering POLYGON's bbox, top-left origin.
    transform = from_origin(-120.1, 36.91, 0.0025, 0.0025)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype.name,
        crs="EPSG:4326",
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(data, 1)
        if scales is not None:
            dst.scales = scales
        if offsets is not None:
            dst.offsets = offsets


def test_read_clipped_band_masks_nodata_and_returns_wgs84_bounds(tmp_path):
    from shapely.geometry import mapping

    data = np.array(
        [
            [0, 1000, 2000, 3000],
            [4000, 0, 5000, 6000],
            [7000, 8000, 9000, 1000],
            [2000, 3000, 4000, 5000],
        ],
        dtype="uint16",
    )
    path = tmp_path / "band.tif"
    _write_test_band(path, data)

    band, inside, bounds = sentinel_client._read_clipped_band(
        str(path), mapping(POLYGON)
    )

    assert band.shape == (4, 4)
    assert inside.all()  # polygon is the full bbox
    # nodata pixels (DN=0) must not survive as zeros
    assert np.isnan(band[0, 0]) and np.isnan(band[1, 1])
    assert band[0, 1] == pytest.approx(1000.0)
    south, west, north, east = bounds
    assert (south, west) == (pytest.approx(36.9), pytest.approx(-120.1))
    assert (north, east) == (pytest.approx(36.91), pytest.approx(-120.09))


def test_read_clipped_band_applies_scale_and_offset(tmp_path):
    from shapely.geometry import mapping

    data = np.full((4, 4), 2000, dtype="uint16")
    path = tmp_path / "band.tif"
    _write_test_band(path, data, scales=(0.0001,), offsets=(-0.1,))

    band, _, _ = sentinel_client._read_clipped_band(str(path), mapping(POLYGON))

    assert band[0, 0] == pytest.approx(0.1)  # 2000 * 0.0001 - 0.1
