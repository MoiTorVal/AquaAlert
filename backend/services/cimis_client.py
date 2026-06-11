"""CIMIS (California Irrigation Management Information System) API client.

Spatial CIMIS publishes daily reference ET (ETo) for any CA coordinate with
~1-day lag — the scheduler uses it to bridge OpenET's ~5-7 day lag with
provisional readings. Free API, key via https://et.water.ca.gov.
"""
import asyncio
import logging
from datetime import date

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

CIMIS_BASE_URL = "https://et.water.ca.gov"
DATA_PATH = "/api/data"
# Spatial CIMIS daily ASCE-standardized reference ET — the only data item
# available for arbitrary lat/lng targets (station items need a station id).
DATA_ITEM = "day-asce-eto"
# response key for DATA_ITEM ("day-asce-eto" comes back as "DayAsceEto")
DATA_ITEM_RESPONSE_KEY = "DayAsceEto"
REQUEST_TIMEOUT_S = 30.0
MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 1.0


class CimisError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class CimisAuthError(CimisError):
    pass


class CimisRequestError(CimisError):
    pass


class CimisUnavailableError(CimisError):
    pass


def _error_detail(response: httpx.Response) -> str:
    return f"CIMIS returned {response.status_code}: {response.text[:200]}"


def _parse_records(data) -> list[dict]:
    """Flatten the nested CIMIS envelope to [{"reading_date", "eto_mm"}, ...].

    Shape: {"Data": {"Providers": [{"Records": [{"Date": ..., "DayAsceEto":
    {"Value": ...}}]}]}}. Records with a missing value (not yet published or
    QC-rejected) are skipped — the gap simply stays open until tomorrow's run.
    """
    try:
        providers = data["Data"]["Providers"]
    except (KeyError, TypeError) as exc:
        raise CimisRequestError(f"Unexpected CIMIS response shape: {data!r:.200}") from exc
    points = []
    for provider in providers:
        for record in provider.get("Records", []):
            try:
                reading_date = date.fromisoformat(record["Date"])
                value = record[DATA_ITEM_RESPONSE_KEY]["Value"]
            except (KeyError, TypeError, ValueError) as exc:
                raise CimisRequestError(f"Unexpected CIMIS record shape: {record!r:.200}") from exc
            if value is None:
                continue
            try:
                eto_mm = float(value)
            except ValueError as exc:
                raise CimisRequestError(f"Non-numeric CIMIS ETo value: {value!r}") from exc
            points.append({"reading_date": reading_date, "eto_mm": eto_mm})
    points.sort(key=lambda p: p["reading_date"])
    return points


async def fetch_daily_eto(
    lat: float,
    lng: float,
    start_date: date,
    end_date: date,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[dict]:
    """Fetch daily Spatial CIMIS reference ET (mm) for a coordinate.

    Returns [{"reading_date": date, "eto_mm": float}, ...] sorted by date.
    Days CIMIS has not published yet are absent. Raises CimisError subclasses.
    """
    if settings.cimis_app_key is None:
        raise CimisAuthError("CIMIS_APP_KEY is not configured")
    params = {
        "appKey": settings.cimis_app_key.get_secret_value(),
        "targets": f"{lat},{lng}",
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dataItems": DATA_ITEM,
        "unitOfMeasure": "M",
    }

    last_error: CimisError | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(
                base_url=CIMIS_BASE_URL, timeout=REQUEST_TIMEOUT_S, transport=transport
            ) as client:
                response = await client.get(DATA_PATH, params=params)
        except httpx.RequestError as exc:
            last_error = CimisUnavailableError(f"CIMIS request failed: {exc}")
            logger.warning("CIMIS request error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)
        else:
            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError:
                    # CIMIS serves HTML error pages with a 200 under load
                    raise CimisRequestError(f"Non-JSON CIMIS response: {response.text[:200]}")
                return _parse_records(payload)
            detail = _error_detail(response)
            if response.status_code in (401, 403):
                raise CimisAuthError(detail, status_code=response.status_code)
            if response.status_code >= 500:
                last_error = CimisUnavailableError(detail, status_code=response.status_code)
                logger.warning("CIMIS server error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, detail)
            else:
                raise CimisRequestError(detail, status_code=response.status_code)
        if attempt < MAX_ATTEMPTS:
            await asyncio.sleep(RETRY_BASE_DELAY_S * 2 ** (attempt - 1))
    if last_error is None:
        raise CimisUnavailableError("Unknown CIMIS error")
    raise last_error
