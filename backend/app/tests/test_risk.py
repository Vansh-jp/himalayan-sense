from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.crud.crud_incident import create_incident, update_incident_status
from app.crud.crud_weather import create_weather_reading
from app.schemas.incident import IncidentCreate
from app.schemas.weather import WeatherReadingCreate
from app.services.risk_service import calculate_zone_risk


def test_rule_based_risk_calculation(db, sample_zone):
    # Base risk without rain
    risk = calculate_zone_risk(db, sample_zone)
    assert risk.risk_level in ["green", "yellow", "orange", "red"]
    assert 0.0 <= risk.risk_score <= 100.0
    assert "formula" in risk.explanation


def test_forecast_rainfall_over_70mm_triggers_red_risk(db, sample_zone):
    # Add weather with forecast rainfall 80mm
    create_weather_reading(
        db,
        WeatherReadingCreate(
            zone_id=sample_zone.id,
            timestamp=datetime.now(timezone.utc),
            precipitation_mm=30.0,
            forecast_precipitation_24h_mm=85.0,
            source="test",
        ),
    )

    risk = calculate_zone_risk(db, sample_zone)
    assert risk.risk_level == "red"
    assert risk.risk_score >= 80.0
    assert any("Dangerous 24h precipitation forecast" in reason for reason in risk.explanation.get("override_reasons", []))


def test_two_verified_landslides_triggers_minimum_orange_risk(db, sample_zone, citizen_user):
    for i in range(2):
        inc = create_incident(
            db,
            IncidentCreate(
                category="landslide",
                description=f"Verified landslide number {i+1}",
                latitude=sample_zone.latitude,
                longitude=sample_zone.longitude,
                severity="high",
                zone_id=sample_zone.id,
            ),
            user_id=citizen_user.id,
        )
        update_incident_status(db, inc, status="verified")

    risk = calculate_zone_risk(db, sample_zone)
    assert risk.risk_level in ["orange", "red"]
    assert any("verified active landslides" in r for r in risk.explanation.get("override_reasons", []))


def test_risk_map_endpoint(client: TestClient, sample_zone):
    response = client.get("/api/v1/risk/map")
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert len(data["features"]) >= 1
    feat = data["features"][0]
    assert "risk_level" in feat
    assert "risk_color" in feat
    assert "boundary_geojson" in feat


def test_risk_recalculate_endpoint(client: TestClient):
    response = client.post("/api/v1/risk/recalculate")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
