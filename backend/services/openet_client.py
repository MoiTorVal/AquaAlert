import asyncio
import logging
from datetime import date, timedelta

import httpx
from shapely.geometry import Polygon

from backend.config import settings

logger = logging.getLogger(__name__)

OPENET_BASE_URL = "https://openet-api.org"
POLYGON_TIMESERIES_PATH = "/raster/timeseries/polygon"
ET_SOURCE = "openet:Ensemble"
REQUEST_TIMEOUT_S = 30.0
MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 1.0
GAPFILL_WINDOW_DAYS = 10


class OpenETError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class OpenETAuthError(OpenETError):
    pass


class OpenETRateLimitError(OpenETError):
    pass


class OpenETRequestError(OpenETError):
    pass


class OpenETUnavailableError(OpenETError):
    pass


def polygon_to_geometry(polygon: Polygon) -> list[float]:
    """Flatten a polygon exterior ring to OpenET's [lon1, lat1, lon2, lat2, ...] format.

    The ring must be open — OpenET rejects a repeated closing point with 400
    "Invalid geometry" (confirmed against the live API 2026-06-09).
    """
    coords = list(polygon.exterior.coords)
    if coords[0] == coords[-1]:
        coords = coords[:-1]
    return [coord for point in coords for coord in point]


def trim_gapfill_tail(points: list[dict], today: date | None = None) -> list[dict]:
    """Drop OpenET's recent-day padding before caching.

    For dates not yet processed, OpenET repeats the last real value to the end
    of the requested range. Cached rows are never refetched, so storing the
    padding would freeze provisional values. Trims the trailing identical run
    down to its first occurrence — but only when the series ends within
    GAPFILL_WINDOW_DAYS of today; historical series can legitimately repeat
    and refetching them would burn quota on every request.
    """
    if len(points) < 2:
        return points
    if today is None:
        today = date.today()
    if points[-1]["reading_date"] < today - timedelta(days=GAPFILL_WINDOW_DAYS):
        return points
    first_of_run = len(points) - 1
    while first_of_run > 0 and points[first_of_run - 1]["et_mm"] == points[-1]["et_mm"]:
        first_of_run -= 1
    return points[: first_of_run + 1]


def _build_payload(geometry: list[float], start_date: date, end_date: date) -> dict:
    return {
        "date_range": [start_date.isoformat(), end_date.isoformat()],
        "interval": "daily",
        "geometry": geometry,
        "model": "Ensemble",
        "variable": "ET",
        "reference_et": "gridMET",
        "units": "mm",
        "reducer": "mean",
        "file_format": "JSON",
        "version": "2.1",
    }


def _error_detail(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    if not isinstance(detail, str):
        detail = response.text[:200]
    return f"OpenET returned {response.status_code}: {detail}"


def _parse_timeseries(data) -> list[dict]:
    if not isinstance(data, list):
        raise OpenETRequestError(f"Unexpected OpenET response shape: {type(data).__name__}")
    points = []
    for entry in data:
        try:
            reading_date = date.fromisoformat(entry["time"])
            et = entry["et"]
        except (KeyError, TypeError, ValueError) as exc:
            raise OpenETRequestError(f"Unexpected OpenET entry shape: {entry!r}") from exc
        if et is None:
            continue
        points.append({"reading_date": reading_date, "et_mm": float(et)})
    return points


async def fetch_daily_et(
    geometry: list[float],
    start_date: date,
    end_date: date,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[dict]:
    """Fetch daily area-averaged ET (mm) for a field polygon from OpenET.

    Returns [{"reading_date": date, "et_mm": float}, ...]. Recent days may be
    absent due to OpenET's ~5-7 day data lag. Raises OpenETError subclasses.
    """
    if settings.openet_api_key is None:
        raise OpenETAuthError("OPENET_API_KEY is not configured")
    # OpenET expects the raw key in Authorization — no "Bearer" prefix.
    headers = {"Authorization": settings.openet_api_key.get_secret_value()}
    payload = _build_payload(geometry, start_date, end_date)

    last_error: OpenETError | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(
                base_url=OPENET_BASE_URL, timeout=REQUEST_TIMEOUT_S, transport=transport
            ) as client:
                response = await client.post(POLYGON_TIMESERIES_PATH, json=payload, headers=headers)
        except httpx.RequestError as exc:
            last_error = OpenETUnavailableError(f"OpenET request failed: {exc}")
            logger.warning("OpenET request error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)
        else:
            if response.status_code == 200:
                return _parse_timeseries(response.json())
            detail = _error_detail(response)
            if response.status_code in (401, 403):
                raise OpenETAuthError(detail, status_code=response.status_code)
            if response.status_code == 429:
                # Monthly quota — retrying only burns more of it.
                raise OpenETRateLimitError(detail, status_code=response.status_code)
            if response.status_code >= 500:
                last_error = OpenETUnavailableError(detail, status_code=response.status_code)
                logger.warning("OpenET server error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, detail)
            else:
                raise OpenETRequestError(detail, status_code=response.status_code)
        if attempt < MAX_ATTEMPTS:
            await asyncio.sleep(RETRY_BASE_DELAY_S * 2 ** (attempt - 1))
    raise last_error
