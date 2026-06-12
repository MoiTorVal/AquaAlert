import asyncio
import json
from datetime import date, timedelta

import httpx
import pytest
from pydantic import SecretStr
from shapely import wkt as shapely_wkt

from backend import crud
from backend.config import settings
from backend.schemas import ETReadingCreate, FarmCreate
from backend.services import openet_client
from backend.services.openet_client import (
    ET_SOURCE,
    OpenETAuthError,
    OpenETRateLimitError,
    OpenETRequestError,
    OpenETUnavailableError,
    fetch_daily_et,
    polygon_to_geometry,
)

POLYGON_WKT = "POLYGON ((-120.5 36.5, -120.4 36.5, -120.4 36.6, -120.5 36.6, -120.5 36.5))"
# open ring: OpenET rejects a repeated closing point
GEOMETRY = [-120.5, 36.5, -120.4, 36.5, -120.4, 36.6, -120.5, 36.6]


@pytest.fixture(autouse=True)
def openet_key(monkeypatch):
    monkeypatch.setattr(settings, "openet_api_key", SecretStr("test-openet-key"))
    monkeypatch.setattr(openet_client, "RETRY_BASE_DELAY_S", 0)


def _fetch(transport, start=date(2026, 5, 1), end=date(2026, 5, 3)):
    return asyncio.run(fetch_daily_et(GEOMETRY, start, end, transport=transport))


def _json_response(payload, status_code=200):
    return httpx.Response(status_code, json=payload)


# ── openet_client ────────────────────────────────────────────────────────────


def test_polygon_to_geometry_flat_open_ring():
    polygon = shapely_wkt.loads(POLYGON_WKT)
    assert polygon_to_geometry(polygon) == GEOMETRY


def test_fetch_parses_timeseries_and_skips_null_et():
    transport = httpx.MockTransport(lambda req: _json_response([
        {"time": "2026-05-01", "et": 0.669},
        {"time": "2026-05-02", "et": None},
        {"time": "2026-05-03", "et": 1.2},
    ]))
    points = _fetch(transport)
    assert points == [
        {"reading_date": date(2026, 5, 1), "et_mm": 0.669},
        {"reading_date": date(2026, 5, 3), "et_mm": 1.2},
    ]


def test_fetch_sends_raw_key_and_pinned_payload():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["Authorization"]
        seen["payload"] = json.loads(request.content)
        return _json_response([])

    _fetch(httpx.MockTransport(handler))
    assert seen["auth"] == "test-openet-key"  # raw key, no Bearer prefix
    assert seen["payload"]["date_range"] == ["2026-05-01", "2026-05-03"]
    assert seen["payload"]["geometry"] == GEOMETRY
    assert seen["payload"]["model"] == "Ensemble"
    assert seen["payload"]["interval"] == "daily"
    assert seen["payload"]["units"] == "mm"
    assert seen["payload"]["reducer"] == "mean"
    assert seen["payload"]["version"] == "2.1"


def test_fetch_missing_key_raises_auth_error(monkeypatch):
    monkeypatch.setattr(settings, "openet_api_key", None)
    with pytest.raises(OpenETAuthError):
        _fetch(httpx.MockTransport(lambda req: _json_response([])))


def test_fetch_401_raises_auth_error_without_retry():
    calls = []

    def handler(request):
        calls.append(request)
        return _json_response({"detail": "invalid key"}, status_code=401)

    with pytest.raises(OpenETAuthError):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == 1


def test_fetch_429_raises_rate_limit_without_retry():
    calls = []

    def handler(request):
        calls.append(request)
        return _json_response({"detail": "quota exceeded"}, status_code=429)

    with pytest.raises(OpenETRateLimitError):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == 1


def test_fetch_400_raises_request_error_with_detail():
    detail = "Single query area limit exceeded. Region must not exceed 50000 acres."
    transport = httpx.MockTransport(
        lambda req: _json_response({"detail": detail}, status_code=400)
    )
    with pytest.raises(OpenETRequestError, match="50000 acres"):
        _fetch(transport)


def test_fetch_500_retries_then_succeeds():
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) < 3:
            return _json_response({"detail": "server error"}, status_code=500)
        return _json_response([{"time": "2026-05-01", "et": 0.5}])

    points = _fetch(httpx.MockTransport(handler))
    assert len(calls) == 3
    assert points[0]["et_mm"] == 0.5


def test_fetch_network_errors_exhaust_retries():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectError("connection refused")

    with pytest.raises(OpenETUnavailableError):
        _fetch(httpx.MockTransport(handler))
    assert len(calls) == openet_client.MAX_ATTEMPTS


def test_fetch_unexpected_shape_raises_request_error():
    transport = httpx.MockTransport(lambda req: _json_response({"unexpected": "shape"}))
    with pytest.raises(OpenETRequestError):
        _fetch(transport)


def test_fetch_malformed_entry_raises_request_error():
    transport = httpx.MockTransport(lambda req: _json_response([{"time": "not-a-date", "et": 1.0}]))
    with pytest.raises(OpenETRequestError):
        _fetch(transport)


def _point(d, et):
    return {"reading_date": d, "et_mm": et}


def test_trim_gapfill_tail_trims_recent_padding():
    today = date(2026, 6, 9)
    points = [
        _point(date(2026, 6, 4), 3.6),
        _point(date(2026, 6, 5), 4.0),
        _point(date(2026, 6, 6), 3.5),
        _point(date(2026, 6, 7), 3.5),
        _point(date(2026, 6, 8), 3.5),
        _point(date(2026, 6, 9), 3.5),
    ]
    trimmed = openet_client.trim_gapfill_tail(points, today=today)
    assert trimmed[-1] == _point(date(2026, 6, 6), 3.5)
    assert len(trimmed) == 3


def test_trim_gapfill_tail_leaves_historical_series():
    today = date(2026, 6, 9)
    points = [
        _point(date(2026, 1, 1), 1.1),
        _point(date(2026, 1, 2), 1.5),
        _point(date(2026, 1, 3), 1.5),
    ]
    assert openet_client.trim_gapfill_tail(points, today=today) == points


def test_trim_gapfill_tail_keeps_mid_series_repeats():
    today = date(2026, 6, 9)
    points = [
        _point(date(2026, 6, 5), 3.5),
        _point(date(2026, 6, 6), 3.5),
        _point(date(2026, 6, 7), 4.0),
    ]
    assert openet_client.trim_gapfill_tail(points, today=today) == points


def test_trim_gapfill_tail_short_series_untouched():
    assert openet_client.trim_gapfill_tail([]) == []
    single = [_point(date.today(), 3.5)]
    assert openet_client.trim_gapfill_tail(single) == single


def test_fetch_non_json_error_body_uses_text():
    transport = httpx.MockTransport(
        lambda req: httpx.Response(400, text="<html>Bad Gateway</html>")
    )
    with pytest.raises(OpenETRequestError, match="Bad Gateway"):
        _fetch(transport)


# ── GET /farms/{id}/et ───────────────────────────────────────────────────────


@pytest.fixture
def polygon_farm(db, user):
    return crud.create_farm(
        db,
        FarmCreate(name="ET Farm", field_polygon=POLYGON_WKT),
        user_id=user.id,
    )


def _seed_et(db, farm_id, days):
    crud.create_et_readings(db, [
        ETReadingCreate(farm_id=farm_id, reading_date=d, et_mm=1.0, source=ET_SOURCE)
        for d in days
    ])


def _fake_fetch(points, calls=None):
    async def fake(geometry, start_date, end_date):
        if calls is not None:
            calls.append((geometry, start_date, end_date))
        return points
    return fake


def test_et_unknown_farm(client):
    response = client.get("/farms/9999/et", params={"from": "2026-05-01", "to": "2026-05-03"})
    assert response.status_code == 404


def test_et_requires_polygon(client, farm):
    response = client.get(f"/farms/{farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-03"})
    assert response.status_code == 400


def test_et_to_before_from_rejected(client, polygon_farm):
    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-03", "to": "2026-05-01"}
    )
    assert response.status_code == 422


def test_et_range_over_366_days_rejected(client, polygon_farm):
    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2025-01-01", "to": "2026-05-01"}
    )
    assert response.status_code == 422


def test_et_cache_hit_skips_fetch(client, db, polygon_farm, monkeypatch):
    days = [date(2026, 5, 1) + timedelta(days=i) for i in range(3)]
    _seed_et(db, polygon_farm.id, days)

    async def boom(*args, **kwargs):
        raise AssertionError("OpenET must not be called on a full cache hit")

    monkeypatch.setattr(openet_client, "fetch_daily_et", boom)
    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-03"}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 3
    assert body["as_of"] == "2026-05-03"


def test_et_cache_only_never_fetches_despite_missing_days(
    client, db, polygon_farm, monkeypatch
):
    # Only 2 of 5 requested days are cached — cache_only must serve the
    # partial result without spending an OpenET request.
    _seed_et(db, polygon_farm.id, [date(2026, 5, 1), date(2026, 5, 2)])

    async def boom(*args, **kwargs):
        raise AssertionError("OpenET must not be called when cache_only=true")

    monkeypatch.setattr(openet_client, "fetch_daily_et", boom)
    response = client.get(
        f"/farms/{polygon_farm.id}/et",
        params={"from": "2026-05-01", "to": "2026-05-05", "cache_only": "true"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    assert body["as_of"] == "2026-05-02"


def test_et_cache_miss_fetches_and_caches(client, db, polygon_farm, monkeypatch):
    calls = []
    points = [
        {"reading_date": date(2026, 5, 1), "et_mm": 0.5},
        {"reading_date": date(2026, 5, 2), "et_mm": 0.7},
    ]
    monkeypatch.setattr(openet_client, "fetch_daily_et", _fake_fetch(points, calls))

    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-02"}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    assert body["results"][0]["source"] == ET_SOURCE
    assert len(calls) == 1

    # second request: fully cached, no second fetch
    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-02"}
    )
    assert response.status_code == 200
    assert len(calls) == 1
    assert len(crud.get_et_readings_by_farm(db, polygon_farm.id)) == 2


def test_et_partial_cache_fetches_only_missing_span(client, db, polygon_farm, monkeypatch):
    _seed_et(db, polygon_farm.id, [date(2026, 5, 1), date(2026, 5, 2)])
    calls = []
    points = [{"reading_date": date(2026, 5, 3), "et_mm": 0.9}]
    monkeypatch.setattr(openet_client, "fetch_daily_et", _fake_fetch(points, calls))

    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-03"}
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 3
    assert len(calls) == 1
    _, fetch_start, fetch_end = calls[0]
    assert fetch_start == date(2026, 5, 3)
    assert fetch_end == date(2026, 5, 3)


def test_et_dedupes_dates_already_cached(client, db, polygon_farm, monkeypatch):
    _seed_et(db, polygon_farm.id, [date(2026, 5, 2)])
    # provider returns a date we already hold — must not insert a duplicate
    points = [
        {"reading_date": date(2026, 5, 1), "et_mm": 0.5},
        {"reading_date": date(2026, 5, 2), "et_mm": 0.6},
        {"reading_date": date(2026, 5, 3), "et_mm": 0.7},
    ]
    monkeypatch.setattr(openet_client, "fetch_daily_et", _fake_fetch(points))

    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-03"}
    )
    assert response.status_code == 200
    readings = crud.get_et_readings_by_farm(db, polygon_farm.id)
    assert len(readings) == 3
    assert [r.reading_date for r in readings] == [date(2026, 5, 1), date(2026, 5, 2), date(2026, 5, 3)]


def test_et_lag_returns_partial_with_as_of(client, db, polygon_farm, monkeypatch):
    # provider has nothing for the most recent days (data lag)
    points = [{"reading_date": date(2026, 5, 1), "et_mm": 0.5}]
    monkeypatch.setattr(openet_client, "fetch_daily_et", _fake_fetch(points))

    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-05"}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 1
    assert body["as_of"] == "2026-05-01"


def test_et_future_only_range_returns_empty_without_fetch(client, polygon_farm, monkeypatch):
    async def boom(*args, **kwargs):
        raise AssertionError("OpenET must not be called for future dates")

    monkeypatch.setattr(openet_client, "fetch_daily_et", boom)
    start = date.today() + timedelta(days=1)
    end = date.today() + timedelta(days=3)
    response = client.get(
        f"/farms/{polygon_farm.id}/et",
        params={"from": start.isoformat(), "to": end.isoformat()},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert body["as_of"] is None


def test_et_rate_limit_maps_to_503(client, polygon_farm, monkeypatch):
    async def fake(*args, **kwargs):
        raise OpenETRateLimitError("quota exceeded", status_code=429)

    monkeypatch.setattr(openet_client, "fetch_daily_et", fake)
    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-03"}
    )
    assert response.status_code == 503


def test_et_provider_error_maps_to_502(client, polygon_farm, monkeypatch):
    async def fake(*args, **kwargs):
        raise OpenETUnavailableError("server error", status_code=500)

    monkeypatch.setattr(openet_client, "fetch_daily_et", fake)
    response = client.get(
        f"/farms/{polygon_farm.id}/et", params={"from": "2026-05-01", "to": "2026-05-03"}
    )
    assert response.status_code == 502
