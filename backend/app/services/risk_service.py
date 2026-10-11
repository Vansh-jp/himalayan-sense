from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.crud.crud_incident import get_incidents
from app.crud.crud_risk import create_risk_assessment, get_latest_risk_for_zone
from app.crud.crud_weather import get_latest_reading_for_zone, get_recent_readings_for_zone
from app.crud.crud_zone import get_zone, get_zones
from app.ml.predict import predict_risk
from app.models.incident import Incident
from app.models.risk import RiskAssessment
from app.models.zone import Zone
from app.schemas.risk import RiskAssessmentCreate
from app.services.alert_service import create_risk_alert_if_needed

logger = logging.getLogger(__name__)

COLOR_MAP = {
    "green": "#22c55e",
    "yellow": "#eab308",
    "orange": "#f97316",
    "red": "#ef4444",
}


def calculate_zone_risk(db: Session, zone: Zone) -> RiskAssessment:
    """Calculate combined rule-based + ML risk for a zone."""
    # 1. Gather Weather Readings
    latest_weather = get_latest_reading_for_zone(db, zone.id)
    recent_readings = get_recent_readings_for_zone(db, zone.id, hours=24)
    recent_readings_72h = get_recent_readings_for_zone(db, zone.id, hours=72)
    recent_readings_3h = get_recent_readings_for_zone(db, zone.id, hours=3)

    rainfall_24h = sum(r.precipitation_mm for r in recent_readings) if recent_readings else 0.0
    rainfall_72h = sum(r.precipitation_mm for r in recent_readings_72h) if recent_readings_72h else rainfall_24h
    rainfall_3h = sum(r.precipitation_mm for r in recent_readings_3h) if recent_readings_3h else 0.0
    forecast_24h = latest_weather.forecast_precipitation_24h_mm if latest_weather and latest_weather.forecast_precipitation_24h_mm else 0.0
    max_hourly_rain = max([r.precipitation_mm for r in recent_readings], default=0.0)

    # 2. Gather Incidents in Zone
    active_incidents = get_incidents(db, zone_id=zone.id, limit=200)
    verified_reports = [i for i in active_incidents if i.status in ["verified", "in_progress"]]
    verified_landslides = [i for i in verified_reports if i.category == "landslide"]
    verified_floods = [i for i in verified_reports if i.category == "flood"]

    # 3. Rule-based Component Scores (0 to 100)
    # 70mm rainfall benchmark for severe Himalayan deluge
    rainfall_24h_score = min(100.0, (rainfall_24h / 70.0) * 100.0)
    forecast_rainfall_24h_score = min(100.0, (forecast_24h / 70.0) * 100.0)
    terrain_susceptibility_score = float(zone.terrain_susceptibility_score * 100.0)
    historical_incident_score = min(100.0, (zone.historical_incident_count / 10.0) * 100.0)
    verified_citizen_report_score = min(100.0, (len(verified_reports) / 5.0) * 100.0)

    # Formula:
    # 0.40 * rainfall_24h + 0.25 * forecast + 0.15 * terrain + 0.10 * historical + 0.10 * citizen
    base_score = (
        0.40 * rainfall_24h_score
        + 0.25 * forecast_rainfall_24h_score
        + 0.15 * terrain_susceptibility_score
        + 0.10 * historical_incident_score
        + 0.10 * verified_citizen_report_score
    )

    override_reasons: List[str] = []
    final_score = base_score

    # Terrain mitigation rule: If rainfall is high but terrain susceptibility is low (< 0.35), reduce score
    if (rainfall_24h >= 35.0 or forecast_24h >= 35.0) and zone.terrain_susceptibility_score < 0.35:
        final_score *= 0.85
        override_reasons.append("Terrain mitigation applied (low slope & stable geology)")

    # Base risk level from score
    if final_score < 25.0:
        risk_level = "green"
    elif final_score < 50.0:
        risk_level = "yellow"
    elif final_score < 75.0:
        risk_level = "orange"
    else:
        risk_level = "red"

    # Strict domain override rules:
    # Rule 1: Verified landslides >= 2 -> minimum Orange
    if len(verified_landslides) >= 2:
        if risk_level in ["green", "yellow"]:
            risk_level = "orange"
            final_score = max(final_score, 55.0)
        override_reasons.append(f"{len(verified_landslides)} verified active landslides in zone (Minimum Orange applied)")

    # Rule 2: Verified floods >= 3 -> minimum Orange
    if len(verified_floods) >= 3:
        if risk_level in ["green", "yellow"]:
            risk_level = "orange"
            final_score = max(final_score, 55.0)
        override_reasons.append(f"{len(verified_floods)} verified active flash-floods in zone (Minimum Orange applied)")

    # Rule 3: Forecast rainfall > 70 mm -> minimum Red
    if forecast_24h > 70.0:
        risk_level = "red"
        final_score = max(final_score, 82.0)
        override_reasons.append(f"Dangerous 24h precipitation forecast ({forecast_24h:.1f} mm > 70 mm) (Minimum Red applied)")

    # 4. ML Model Evaluation
    ml_features = {
        "rainfall_last_3h": rainfall_3h,
        "rainfall_last_24h": rainfall_24h,
        "rainfall_last_72h": rainfall_72h,
        "forecast_rainfall_24h": forecast_24h,
        "max_hourly_rainfall": max_hourly_rain,
        "slope": 35.0 if zone.terrain_susceptibility_score > 0.6 else 18.0,
        "elevation": 720.0,
        "distance_to_river": 350.0 if zone.terrain_susceptibility_score > 0.5 else 1200.0,
        "road_density": 3.2,
        "historical_incident_count": zone.historical_incident_count,
        "active_verified_reports": len(verified_reports),
    }
    ml_result = predict_risk(ml_features)

    # Integrate ML probability: if ML flags high risk and current level is green, promote to yellow/orange
    if ml_result.get("is_high_risk") and risk_level == "green":
        risk_level = "yellow"
        final_score = max(final_score, 35.0)
        override_reasons.append(f"ML Model ({ml_result.get('model_name')}) flagged elevated risk probability ({ml_result.get('risk_probability'):.2f})")

    primary_risk_type = "landslide"
    if len(verified_floods) > len(verified_landslides):
        primary_risk_type = "flood"
    elif any(i.category == "road_block" for i in verified_reports):
        primary_risk_type = "road_block"

    explanation = {
        "formula": "0.40*rain24h + 0.25*forecast24h + 0.15*terrain + 0.10*history + 0.10*reports",
        "components": {
            "rainfall_24h_mm": round(rainfall_24h, 2),
            "rainfall_24h_score": round(rainfall_24h_score, 2),
            "forecast_rainfall_24h_mm": round(forecast_24h, 2),
            "forecast_rainfall_24h_score": round(forecast_rainfall_24h_score, 2),
            "terrain_susceptibility_score": round(terrain_susceptibility_score, 2),
            "historical_incident_score": round(historical_incident_score, 2),
            "verified_citizen_reports_count": len(verified_reports),
            "verified_citizen_report_score": round(verified_citizen_report_score, 2),
            "base_score": round(base_score, 2),
            "final_score": round(final_score, 2),
        },
        "override_reasons": override_reasons,
        "ml_inference": ml_result,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    assessment_in = RiskAssessmentCreate(
        zone_id=zone.id,
        risk_type=primary_risk_type,
        risk_score=round(final_score, 2),
        risk_level=risk_level,
        model_version=ml_result.get("model_version", "rule_v1"),
        explanation=explanation,
    )
    assessment = create_risk_assessment(db, assessment_in)

    # Check alert dispatch
    create_risk_alert_if_needed(db, zone, assessment)

    return assessment


def recalculate_all_zones_risk(db: Session) -> Dict[str, Any]:
    zones = get_zones(db, limit=200)
    created = 0
    for zone in zones:
        try:
            calculate_zone_risk(db, zone)
            created += 1
        except Exception as e:
            logger.error(f"Error evaluating risk for zone {zone.name}: {e}")

    return {
        "status": "success",
        "zones_evaluated": len(zones),
        "assessments_created": created,
        "alerts_generated": created,
        "timestamp": datetime.now(timezone.utc),
    }
