from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.crud_incident import get_incidents
from app.crud.crud_risk import get_latest_risk_for_zone, get_risk_history
from app.crud.crud_weather import get_latest_reading_for_zone, get_recent_readings_for_zone
from app.crud.crud_zone import get_zones
from app.schemas.risk import (
    RiskAssessmentOut,
    RiskMapFeature,
    RiskMapResponse,
    RiskRecalculateResponse,
)
from app.services.risk_service import (
    COLOR_MAP,
    calculate_zone_risk,
    recalculate_all_zones_risk,
)

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


@router.get("/map", response_model=RiskMapResponse)
def get_risk_map_data(db: Session = Depends(get_db)):
    """Interactive Leaflet map feed showing all pilot zones, risk levels, colors, rainfall, and active incidents."""
    zones = get_zones(db, limit=100)
    features: List[RiskMapFeature] = []

    for zone in zones:
        risk = get_latest_risk_for_zone(db, zone.id)
        if not risk:
            risk = calculate_zone_risk(db, zone)

        recent_readings = get_recent_readings_for_zone(db, zone.id, hours=24)
        rain_24h = sum(r.precipitation_mm for r in recent_readings) if recent_readings else 0.0
        latest_weather = get_latest_reading_for_zone(db, zone.id)
        forecast_24h = latest_weather.forecast_precipitation_24h_mm if latest_weather and latest_weather.forecast_precipitation_24h_mm else 0.0

        active_incidents = get_incidents(db, zone_id=zone.id, limit=200)
        active_count = len([i for i in active_incidents if i.status in ["submitted", "verified", "in_progress"]])

        explanation_dict = risk.explanation if isinstance(risk.explanation, dict) else {}
        reasons = explanation_dict.get("override_reasons", [])
        summary_note = "; ".join(reasons) if reasons else f"Score {risk.risk_score:.1f}/100"

        feature = RiskMapFeature(
            zone_id=zone.id,
            name=zone.name,
            district=zone.district,
            risk_level=risk.risk_level,
            risk_color=COLOR_MAP.get(risk.risk_level, "#22c55e"),
            risk_score=risk.risk_score,
            primary_risk_type=risk.risk_type,
            rainfall_last_24h_mm=round(rain_24h, 2),
            forecast_rainfall_24h_mm=round(forecast_24h, 2),
            active_incidents=active_count,
            last_updated=risk.assessed_at,
            explanation_summary=summary_note,
            boundary_geojson=zone.boundary_geojson,
        )
        features.append(feature)

    return RiskMapResponse(
        count=len(features),
        timestamp=datetime.now(timezone.utc),
        features=features,
    )


@router.get("/history", response_model=List[RiskAssessmentOut])
def get_historical_risk_assessments(
    zone_id: Optional[UUID] = Query(None),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return get_risk_history(db, zone_id=zone_id, from_date=from_date, to_date=to_date, limit=limit)


@router.post("/recalculate", response_model=RiskRecalculateResponse)
def recalculate_risk_assessments(db: Session = Depends(get_db)):
    """Triggers risk re-evaluation for all zones across meteorological and incident inputs."""
    result = recalculate_all_zones_risk(db)
    return RiskRecalculateResponse(
        status=result["status"],
        zones_evaluated=result["zones_evaluated"],
        assessments_created=result["assessments_created"],
        alerts_generated=result["alerts_generated"],
        timestamp=result["timestamp"],
    )
