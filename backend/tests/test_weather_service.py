import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from backend.services.weather_service import parse_weather_data, get_weather_data


# ── parse_weather_data ────────────────────────────────────────────────────────


def test_parse_weather_data_none_input_returns_none():
    assert parse_weather_data(None) is None


def test_parse_weather_data_full_response():
    data = {
        "main": {"temp": 25.5, "humidity": 60},
        "weather": [{"description": "clear sky"}],
        "rain": {"1h": 2.5},
        "wind": {"speed": 5.0},
        "name": "Fresno",
        "dt": 1700000000,
    }
    result = parse_weather_data(data)
    assert result is not None
    assert result["temperature_c"] == 25.5
    assert result["humidity_pct"] == 60
    assert result["description"] == "clear sky"
    assert result["rainfall_mm"] == 2.5
    assert result["wind_speed_kph"] == pytest.approx(5.0 * 3.6)
    assert result["location"] == "Fresno"


def test_parse_weather_data_returns_datetime_for_recorded_at():
    data = {
        "main": {"temp": 20.0, "humidity": 50},
        "weather": [{"description": "sunny"}],
        "name": "City",
        "dt": 1700000000,
    }
    result = parse_weather_data(data)
    assert isinstance(result["recorded_at"], datetime)


def test_parse_weather_data_no_rain_key_defaults_to_zero():
    data = {
        "main": {"temp": 20.0, "humidity": 50},
        "weather": [{"description": "sunny"}],
        "wind": {"speed": 3.0},
        "name": "City",
        "dt": 1700000000,
    }
    result = parse_weather_data(data)
    assert result["rainfall_mm"] == 0


def test_parse_weather_data_rain_key_without_1h_defaults_to_zero():
    data = {
        "main": {"temp": 20.0, "humidity": 50},
        "weather": [{"description": "light rain"}],
        "rain": {},  # "1h" subkey is absent
        "wind": {"speed": 3.0},
        "name": "City",
        "dt": 1700000000,
    }
    result = parse_weather_data(data)
    assert result["rainfall_mm"] == 0


def test_parse_weather_data_no_wind_key_defaults_to_zero():
    data = {
        "main": {"temp": 20.0, "humidity": 50},
        "weather": [{"description": "calm"}],
        "name": "City",
        "dt": 1700000000,
    }
    result = parse_weather_data(data)
    assert result["wind_speed_kph"] == 0


def test_parse_weather_data_missing_main_returns_none():
    data = {"weather": [{"description": "fog"}], "dt": 1700000000, "name": "X"}
    result = parse_weather_data(data)
    assert result is None


def test_parse_weather_data_missing_weather_list_returns_none():
    data = {"main": {"temp": 20.0, "humidity": 50}, "name": "City", "dt": 1700000000}
    result = parse_weather_data(data)
    assert result is None


# ── get_weather_data ──────────────────────────────────────────────────────────


def test_get_weather_data_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": "Fresno", "dt": 1700000000}
    with patch("backend.services.weather_service.requests.get", return_value=mock_response):
        result = get_weather_data("Fresno")
    assert result == {"name": "Fresno", "dt": 1700000000}


def test_get_weather_data_non_200_returns_none():
    mock_response = MagicMock()
    mock_response.status_code = 404
    with patch("backend.services.weather_service.requests.get", return_value=mock_response):
        result = get_weather_data("Unknown City")
    assert result is None


def test_get_weather_data_request_exception_returns_none():
    import requests as req_module
    with patch(
        "backend.services.weather_service.requests.get",
        side_effect=req_module.exceptions.RequestException("timeout"),
    ):
        result = get_weather_data("Fresno")
    assert result is None
