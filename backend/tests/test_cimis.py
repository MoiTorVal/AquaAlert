import asyncio
from datetime import date

import httpx
import pytest
from pydantic import SecretStr

from backend.config import settings
from backend.services import cimis_client
from backend.services.cimis_client import (
    CimisAuthError,
    CimisRequestError,
    CimisUnavailableError,
    fetch_daily_eto,
)

LAT, LNG = 36.9, -120.1


@pytest.fixture(autouse=True)
def cimis_key(monkeypatch):
    monkeypatch.setattr(settings, "cimis_app_key", SecretStr("test-cimis-key"))
    monkeypatch.setattr(cimis_client, "RETRY_BASE_DELAY_S", 0)


def _fetch(transport, start=date(2026, 6, 1), end=date(2026, 6, 3)):
    return asyncio.run(fetch_daily_eto(LAT, LNG, start, end, transport=transport))


def _envelope(records):
    return {"Data": {"Providers": [{"Name": "cimis", "Records": records}]}}


def _record(day, value):
    return {"Date": day, "DayAsceEto": {"Value": value, "Qc": " ", "Unit": "(mm)"}}


def _json_response(payload, status_code=200):
    return httpx.Response(status_code, json=payload)


def test_fetch_parses_records_and_skips_unpublished():
    transport = httpx.MockTransport(lambda req: _json_response(_envelope([
        _record("2026-06-02", "4.81"),
        _record("2026-06-01", "5.43"),
        _record("2026-06-03", None),  # not yet published
    ])))
    points = _fetch(transport)
    assert points == [
        {"reading_date": date(2026, 6, 1), "eto_mm": 5.43},
        {"reading_date": date(2026, 6, 2), "eto_mm": 4.81},
    ]


def test_fetch_sends_key_and_spatial_params():
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return _json_response(_envelope([]))

    _fetch(httpx.MockTransport(handler))
    assert seen["params"] == {
        "appKey": "test-cimis-key",
        "targets": "36.9,-120.1",
        "startDate": "2026-06-01",
        "endDate": "2026-06-03",
        "dataItems": "day-asce-eto",
        "unitOfMeasure": "M",
    }


def test_fetch_missing_key_raises_auth_error(monkeypatch):
    monkeypatch.setattr(settings, "cimis_app_key", None)
    with pytest.raises(CimisAuthError):
        _fetch(httpx.MockTransport(lambda req: _json_response(_envelope([]))))


def test_fetch_403_raises_auth_error_without_retry():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(403, text="invalid app key")

    with pytest.raises(CimisAuthError):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == 1


def test_fetch_400_raises_request_error_without_retry():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(400, text="too many records requested")

    with pytest.raises(CimisRequestError, match="too many records"):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == 1


def test_fetch_5xx_retries_then_raises_unavailable():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503, text="overloaded")

    with pytest.raises(CimisUnavailableError):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == cimis_client.MAX_ATTEMPTS


def test_fetch_transport_error_retries_then_raises_unavailable():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectTimeout("timed out")

    with pytest.raises(CimisUnavailableError):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == cimis_client.MAX_ATTEMPTS


def test_fetch_5xx_then_success_recovers():
    responses = iter([
        httpx.Response(500, text="hiccup"),
        _json_response(_envelope([_record("2026-06-01", "5.0")])),
    ])
    transport = httpx.MockTransport(lambda req: next(responses))
    assert _fetch(transport) == [{"reading_date": date(2026, 6, 1), "eto_mm": 5.0}]


def test_fetch_non_json_200_raises_request_error():
    transport = httpx.MockTransport(
        lambda req: httpx.Response(200, text="<html>maintenance page</html>")
    )
    with pytest.raises(CimisRequestError, match="Non-JSON"):
        _fetch(transport)


def test_fetch_unexpected_envelope_raises_request_error():
    transport = httpx.MockTransport(lambda req: _json_response({"unexpected": True}))
    with pytest.raises(CimisRequestError, match="response shape"):
        _fetch(transport)


def test_fetch_unexpected_record_raises_request_error():
    transport = httpx.MockTransport(
        lambda req: _json_response(_envelope([{"Date": "2026-06-01"}]))
    )
    with pytest.raises(CimisRequestError, match="record shape"):
        _fetch(transport)


def test_fetch_non_numeric_value_raises_request_error():
    transport = httpx.MockTransport(
        lambda req: _json_response(_envelope([_record("2026-06-01", "n/a")]))
    )
    with pytest.raises(CimisRequestError, match="Non-numeric"):
        _fetch(transport)
