import asyncio
from datetime import date

import httpx
import pytest

from backend.services import rainfall_client
from backend.services.rainfall_client import (
    ARCHIVE_URL,
    FORECAST_URL,
    RainfallRequestError,
    RainfallUnavailableError,
    fetch_daily_precip,
)

LAT, LNG = 36.9, -120.1
TODAY = date(2026, 6, 10)
# entirely older than TODAY - ARCHIVE_LAG_DAYS → archive endpoint only
OLD_START, OLD_END = date(2026, 5, 1), date(2026, 5, 3)
# entirely within the lag window → forecast endpoint only
RECENT_START, RECENT_END = date(2026, 6, 7), date(2026, 6, 9)


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr(rainfall_client, "RETRY_BASE_DELAY_S", 0)


def _fetch(transport, start=OLD_START, end=OLD_END):
    return asyncio.run(
        fetch_daily_precip(LAT, LNG, start, end, today=TODAY, transport=transport)
    )


def _daily_payload(times, values):
    return {"daily": {"time": times, "precipitation_sum": values}}


def _json_response(payload, status_code=200):
    return httpx.Response(status_code, json=payload)


def test_fetch_parses_and_skips_unpublished_days():
    transport = httpx.MockTransport(lambda req: _json_response(
        _daily_payload(["2026-05-01", "2026-05-02", "2026-05-03"], [0.0, 5.2, None])
    ))
    assert _fetch(transport) == [
        {"reading_date": date(2026, 5, 1), "precip_mm": 0.0},
        {"reading_date": date(2026, 5, 2), "precip_mm": 5.2},
    ]


def test_fetch_old_range_uses_archive_endpoint_only():
    seen = []

    def handler(request):
        seen.append((str(request.url.copy_with(params=None)), dict(request.url.params)))
        return _json_response(_daily_payload([], []))

    _fetch(httpx.MockTransport(handler))
    assert len(seen) == 1
    url, params = seen[0]
    assert url == ARCHIVE_URL
    assert params["start_date"] == "2026-05-01"
    assert params["end_date"] == "2026-05-03"
    assert params["daily"] == "precipitation_sum"
    assert params["latitude"] == "36.9"
    assert params["longitude"] == "-120.1"


def test_fetch_recent_range_uses_forecast_endpoint_only():
    seen = []

    def handler(request):
        seen.append(str(request.url.copy_with(params=None)))
        return _json_response(_daily_payload([], []))

    _fetch(httpx.MockTransport(handler), start=RECENT_START, end=RECENT_END)
    assert seen == [FORECAST_URL]


def test_fetch_spanning_range_splits_across_endpoints_and_sorts():
    def handler(request):
        url = str(request.url.copy_with(params=None))
        params = dict(request.url.params)
        if url == ARCHIVE_URL:
            assert params["start_date"] == "2026-05-30"
            assert params["end_date"] == "2026-06-04"  # TODAY - ARCHIVE_LAG_DAYS
            return _json_response(_daily_payload(["2026-05-30"], [1.0]))
        assert url == FORECAST_URL
        assert params["start_date"] == "2026-06-05"
        assert params["end_date"] == "2026-06-09"
        return _json_response(_daily_payload(["2026-06-05"], [2.5]))

    points = _fetch(httpx.MockTransport(handler), start=date(2026, 5, 30), end=date(2026, 6, 9))
    assert points == [
        {"reading_date": date(2026, 5, 30), "precip_mm": 1.0},
        {"reading_date": date(2026, 6, 5), "precip_mm": 2.5},
    ]


def test_fetch_400_raises_request_error_without_retry():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(400, text='{"error":true,"reason":"invalid date"}')

    with pytest.raises(RainfallRequestError, match="invalid date"):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == 1


def test_fetch_5xx_retries_then_raises_unavailable():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503, text="overloaded")

    with pytest.raises(RainfallUnavailableError):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == rainfall_client.MAX_ATTEMPTS


def test_fetch_transport_error_retries_then_raises_unavailable():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectTimeout("timed out")

    with pytest.raises(RainfallUnavailableError):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == rainfall_client.MAX_ATTEMPTS


def test_fetch_5xx_then_success_recovers():
    responses = iter([
        httpx.Response(500, text="hiccup"),
        _json_response(_daily_payload(["2026-05-01"], [3.0])),
    ])
    transport = httpx.MockTransport(lambda req: next(responses))
    assert _fetch(transport) == [{"reading_date": date(2026, 5, 1), "precip_mm": 3.0}]


def test_fetch_non_json_200_raises_request_error():
    transport = httpx.MockTransport(
        lambda req: httpx.Response(200, text="<html>maintenance page</html>")
    )
    with pytest.raises(RainfallRequestError, match="Non-JSON"):
        _fetch(transport)


def test_fetch_unexpected_shape_raises_request_error():
    transport = httpx.MockTransport(lambda req: _json_response({"unexpected": True}))
    with pytest.raises(RainfallRequestError, match="response shape"):
        _fetch(transport)


def test_fetch_non_numeric_value_raises_request_error():
    transport = httpx.MockTransport(
        lambda req: _json_response(_daily_payload(["2026-05-01"], ["n/a"]))
    )
    with pytest.raises(RainfallRequestError, match="Bad Open-Meteo record"):
        _fetch(transport)
