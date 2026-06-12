"""Open-Meteo daily precipitation client (free, no API key).

Supplies observed rainfall for the AquaCrop sim's Precipitation input — the
sim previously assumed zero rain. Two endpoints split by age: the ERA5
archive lags ~5 days, so newer days come from the forecast API's modeled
past. Recent values can be revised, so the scheduler re-pulls a trailing
window and upserts.
"""
import asyncio
import logging
from datetime import date, timedelta

import httpx

logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
# ERA5 archive publishes with ~5-day delay; anything newer comes from the
# forecast endpoint (which serves modeled past days up to 92 back).
ARCHIVE_LAG_DAYS = 6
REQUEST_TIMEOUT_S = 30.0
MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 1.0


class RainfallError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RainfallRequestError(RainfallError):
    pass


class RainfallUnavailableError(RainfallError):
    pass


def _parse_daily(data) -> list[dict]:
    """Flatten {"daily": {"time": [...], "precipitation_sum": [...]}} to
    [{"reading_date", "precip_mm"}, ...]. Null values (day not yet published)
    are skipped — the gap stays open until a later run fills it.
    """
    try:
        times = data["daily"]["time"]
        values = data["daily"]["precipitation_sum"]
    except (KeyError, TypeError) as exc:
        raise RainfallRequestError(f"Unexpected Open-Meteo response shape: {data!r:.200}") from exc
    points = []
    for day, value in zip(times, values):
        if value is None:
            continue
        try:
            points.append({"reading_date": date.fromisoformat(day), "precip_mm": float(value)})
        except (TypeError, ValueError) as exc:
            raise RainfallRequestError(f"Bad Open-Meteo record: {day!r}={value!r}") from exc
    return points


async def _get_daily(
    client: httpx.AsyncClient, url: str, lat: float, lng: float, start: date, end: date
) -> list[dict]:
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": "precipitation_sum",
        "timezone": "UTC",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    last_error: RainfallError | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = await client.get(url, params=params)
        except httpx.RequestError as exc:
            last_error = RainfallUnavailableError(f"Open-Meteo request failed: {exc}")
            logger.warning("Open-Meteo request error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)
        else:
            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError:
                    raise RainfallRequestError(f"Non-JSON Open-Meteo response: {response.text[:200]}")
                return _parse_daily(payload)
            detail = f"Open-Meteo returned {response.status_code}: {response.text[:200]}"
            if response.status_code >= 500:
                last_error = RainfallUnavailableError(detail, status_code=response.status_code)
                logger.warning("Open-Meteo server error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, detail)
            else:
                raise RainfallRequestError(detail, status_code=response.status_code)
        if attempt < MAX_ATTEMPTS:
            await asyncio.sleep(RETRY_BASE_DELAY_S * 2 ** (attempt - 1))
    if last_error is None:
        raise RainfallUnavailableError("Unknown Open-Meteo error")
    raise last_error


async def fetch_daily_precip(
    lat: float,
    lng: float,
    start_date: date,
    end_date: date,
    today: date | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[dict]:
    """Fetch observed daily precipitation (mm) for a coordinate.

    Returns [{"reading_date": date, "precip_mm": float}, ...] sorted by date.
    The range is split across the archive (older than ARCHIVE_LAG_DAYS) and
    forecast (recent) endpoints. Raises RainfallError subclasses.
    """
    if today is None:
        today = date.today()
    archive_end = min(end_date, today - timedelta(days=ARCHIVE_LAG_DAYS))
    points: list[dict] = []
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S, transport=transport) as client:
        if start_date <= archive_end:
            points += await _get_daily(client, ARCHIVE_URL, lat, lng, start_date, archive_end)
        recent_start = max(start_date, archive_end + timedelta(days=1))
        if recent_start <= end_date:
            points += await _get_daily(client, FORECAST_URL, lat, lng, recent_start, end_date)
    points.sort(key=lambda p: p["reading_date"])
    return points
