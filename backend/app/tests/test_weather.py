from unittest.mock import patch
from fastapi.testclient import TestClient


def test_weather_ingestion_mocked(client: TestClient, admin_token_headers, sample_zone):
    mock_payload = {
        "hourly": {
            "time": ["2026-10-11T00:00", "2026-10-11T01:00", "2026-10-11T02:00"],
            "precipitation": [5.2, 8.4, 12.0],
            "temperature_2m": [22.0, 21.5, 21.0],
            "relative_humidity_2m": [80.0, 85.0, 90.0],
            "wind_speed_10m": [6.0, 7.5, 8.0],
        }
    }

    with patch("app.services.weather_service.fetch_open_meteo_forecast", return_value=mock_payload):
        resp = client.post(
            f"/api/v1/weather/ingest?zone_id={sample_zone.id}",
            headers=admin_token_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["readings_created"] == 3


def test_get_current_weather(client: TestClient, sample_zone):
    response = client.get(f"/api/v1/weather/current?zone_id={sample_zone.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["zone_name"] == sample_zone.name
    assert "rainfall_last_24h_mm" in data


def test_get_weather_forecast(client: TestClient, sample_zone):
    response = client.get(f"/api/v1/weather/forecast?zone_id={sample_zone.id}")
    assert response.status_code == 200
    data = response.json()
    assert "forecast_next_24h_mm" in data
