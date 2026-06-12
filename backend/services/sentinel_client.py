"""Sentinel-2 NDVI client (free, no API key).

Uses Earth Search STAC + windowed COG reads to compute clipped NDVI for one
farm polygon at native 10 m resolution.
"""
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import numpy as np
from shapely.geometry import Polygon, mapping

logger = logging.getLogger(__name__)

EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1"
S2_COLLECTION = "sentinel-2-l2a"
REQUEST_TIMEOUT_S = 30.0
MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 1.0

try:  # optional dependency: keep app bootable when feature is disabled
    from pystac_client import Client
except Exception:  # pragma: no cover - exercised via dependency guard
    Client = None  # type: ignore[assignment]

try:  # optional dependency: keep app bootable when feature is disabled
    import rasterio
    from rasterio.features import geometry_mask, geometry_window
    from rasterio.warp import transform_bounds, transform_geom
    from rasterio.windows import bounds as window_bounds
except Exception:  # pragma: no cover - exercised via dependency guard
    rasterio = None  # type: ignore[assignment]
    geometry_mask = None  # type: ignore[assignment]
    geometry_window = None  # type: ignore[assignment]
    transform_bounds = None  # type: ignore[assignment]
    transform_geom = None  # type: ignore[assignment]
    window_bounds = None  # type: ignore[assignment]


class SentinelError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class SentinelRequestError(SentinelError):
    pass


class SentinelDependencyError(SentinelError):
    pass


class SentinelUnavailableError(SentinelError):
    pass


def _require_geo_dependencies() -> None:
    if Client is None or rasterio is None:
        raise SentinelDependencyError(
            "Sentinel dependencies are unavailable; install pystac-client and rasterio"
        )


def _search_items(
    polygon: Polygon, lookback_days: int, max_cloud_pct: float
) -> list[Any]:
    _require_geo_dependencies()
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=lookback_days)
    client = Client.open(EARTH_SEARCH_URL)  # type: ignore[operator]
    search = client.search(
        collections=[S2_COLLECTION],
        intersects=mapping(polygon),
        datetime=f"{start.isoformat()}/{end.isoformat()}",
        query={"eo:cloud_cover": {"lte": max_cloud_pct}},
        sortby=[{"field": "properties.datetime", "direction": "desc"}],
        limit=50,
    )
    return list(search.items())


def _pick_scene(items: list[Any], max_cloud_pct: float) -> Any:
    for item in items:
        cloud_cover = item.properties.get("eo:cloud_cover")
        if cloud_cover is None or float(cloud_cover) <= max_cloud_pct:
            return item
    raise SentinelUnavailableError("No acceptable Sentinel-2 scene in lookback window")


def _asset_href(item: Any, candidates: list[str]) -> str:
    for key in candidates:
        asset = item.assets.get(key)
        if asset is not None and getattr(asset, "href", None):
            return str(asset.href)
    raise SentinelRequestError(f"Sentinel item missing required asset(s): {candidates}")


def _read_clipped_band(
    href: str, polygon_geojson: dict
) -> tuple[np.ndarray, np.ndarray, tuple[float, float, float, float]]:
    """Read the polygon's window from one band.

    Returns (band, inside-mask, window bounds as (south, west, north, east) in
    WGS84). Nodata pixels become NaN so a scene edge crossing the field can't
    fake NDVI extremes of +/-1.0, and per-band scale/offset metadata is honored
    (a no-op on plain DN COGs, but newer L2A baselines publish an offset).
    """
    _require_geo_dependencies()
    with rasterio.open(href) as dataset:  # type: ignore[union-attr]
        geom = transform_geom("EPSG:4326", dataset.crs, polygon_geojson)  # type: ignore[misc]
        window = geometry_window(dataset, [geom], pad_x=0, pad_y=0)  # type: ignore[misc]
        band = dataset.read(1, window=window).astype("float32")
        nodata = 0.0 if dataset.nodata is None else float(dataset.nodata)
        band[band == nodata] = np.nan
        scale, offset = float(dataset.scales[0]), float(dataset.offsets[0])
        if scale != 1.0 or offset != 0.0:
            band = band * scale + offset
        transform = dataset.window_transform(window)
        inside = geometry_mask(
            [geom], transform=transform, out_shape=band.shape, invert=True
        )  # type: ignore[misc]
        band[~inside] = np.nan
        west, south, east, north = transform_bounds(  # type: ignore[misc]
            dataset.crs, "EPSG:4326", *window_bounds(window, dataset.transform)  # type: ignore[misc]
        )
        return band, inside, (south, west, north, east)


def _to_grid(ndvi: np.ndarray) -> list[list[float | None]]:
    grid: list[list[float | None]] = []
    for row in ndvi:
        grid.append(
            [None if np.isnan(v) else round(float(v), 3) for v in row]
        )
    return grid


def _compute_ndvi_scan(
    scan_date: date,
    cloud_cover_pct: float | None,
    red: np.ndarray,
    nir: np.ndarray,
    inside: np.ndarray,
    grid_bounds: tuple[float, float, float, float],
) -> dict:
    if red.shape != nir.shape or red.shape != inside.shape:
        raise SentinelRequestError("Sentinel red/nir assets are misaligned")
    denom = nir + red
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = (nir - red) / denom
    ndvi[~inside] = np.nan
    valid = ndvi[~np.isnan(ndvi)]
    if valid.size == 0:
        mean_ndvi = max_ndvi = min_ndvi = None
    else:
        mean_ndvi = round(float(np.mean(valid)), 3)
        max_ndvi = round(float(np.max(valid)), 3)
        min_ndvi = round(float(np.min(valid)), 3)
    south, west, north, east = grid_bounds
    return {
        "scan_date": scan_date,
        "cloud_cover_pct": cloud_cover_pct,
        "mean_ndvi": mean_ndvi,
        "max_ndvi": max_ndvi,
        "min_ndvi": min_ndvi,
        "ndvi_grid": _to_grid(ndvi),
        # Leaflet-style [[south, west], [north, east]] of the raster window.
        # The window is axis-aligned in the scene's UTM CRS, so a small grid-
        # convergence skew (<~1-2 deg in CA) remains after the bbox reproject;
        # storing the true window bbox removes the dominant misalignment.
        "ndvi_grid_bounds": [[south, west], [north, east]],
    }


def fetch_latest_ndvi(
    polygon: Polygon,
    *,
    max_cloud_pct: float = 15,
    lookback_days: int = 14,
) -> dict:
    """Fetch latest acceptable Sentinel-2 scene and compute clipped NDVI."""
    polygon_geojson = mapping(polygon)
    last_error: SentinelError | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            items = _search_items(polygon, lookback_days, max_cloud_pct)
            if not items:
                raise SentinelUnavailableError("No acceptable Sentinel-2 scene in lookback window")
            scene = _pick_scene(items, max_cloud_pct)
            red_href = _asset_href(scene, ["red", "B04"])
            nir_href = _asset_href(scene, ["nir", "B08"])
            red, inside, grid_bounds = _read_clipped_band(red_href, polygon_geojson)
            nir, nir_inside, _ = _read_clipped_band(nir_href, polygon_geojson)
            inside &= nir_inside
            timestamp = scene.properties.get("datetime")
            if not isinstance(timestamp, str):
                raise SentinelRequestError("Sentinel scene missing datetime")
            scan_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date()
            cloud_cover = scene.properties.get("eo:cloud_cover")
            cloud_cover_pct = None if cloud_cover is None else round(float(cloud_cover), 2)
            return _compute_ndvi_scan(
                scan_date, cloud_cover_pct, red, nir, inside, grid_bounds
            )
        except SentinelError:
            raise
        except Exception as exc:
            last_error = SentinelUnavailableError(f"Sentinel request failed: {exc}")
            logger.warning(
                "Sentinel fetch failed (attempt %d/%d): %s",
                attempt,
                MAX_ATTEMPTS,
                exc,
            )
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_BASE_DELAY_S * 2 ** (attempt - 1))
    if last_error is None:
        raise SentinelUnavailableError("Unknown Sentinel error")
    raise last_error
