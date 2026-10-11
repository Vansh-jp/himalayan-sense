from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.crud.crud_alert import create_alert
from app.crud.crud_risk import create_risk_assessment
from app.models.risk import RiskAssessment
from app.schemas.alert import AlertCreate
from app.schemas.risk import RiskAssessmentCreate
from app.services.alert_service import (
    create_risk_alert_if_needed,
    should_send_zone_alert,
)


def test_alert_generation_for_orange_risk(db, sample_zone):
    assessment = RiskAssessment(
        zone_id=sample_zone.id,
        assessed_at=datetime.now(timezone.utc),
        risk_type="landslide",
        risk_score=68.5,
        risk_level="orange",
        model_version="rule_v1",
        explanation={"override_reasons": ["High landslide activity"]},
    )
    db.add(assessment)
    db.commit()

    alert = create_risk_alert_if_needed(db, sample_zone, assessment)
    assert alert is not None
    assert alert.risk_level == "orange"
    assert "High Landslide Risk" in alert.title


def test_deduplication_prevents_duplicate_alert_within_6_hours(db, sample_zone):
    # Initial alert at orange
    create_alert(
        db,
        AlertCreate(
            zone_id=sample_zone.id,
            title="First Alert",
            message="Alert 1",
            risk_level="orange",
            channel="in_app",
            status="sent",
        ),
    )

    # Check if duplicate orange is allowed within 6h -> should be False
    assert should_send_zone_alert(db, sample_zone.id, "orange") is False

    # But escalation to red risk should be allowed -> True
    assert should_send_zone_alert(db, sample_zone.id, "red") is True


def test_list_alerts_endpoint(client: TestClient, sample_zone):
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_subscribe_alerts_endpoint(client: TestClient):
    payload = {
        "email": "subscriber@himalayasense.local",
        "channels": ["in_app", "email"],
    }
    response = client.post("/api/v1/alerts/subscribe", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "subscribed"
