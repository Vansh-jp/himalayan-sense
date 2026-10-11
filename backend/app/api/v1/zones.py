from datetime import datetime, timezone
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.crud.crud_incident import get_incidents
from app.crud.crud_risk import get_latest_risk_for_zone
from app.crud.crud_weather import get_latest_reading_for_zone, get_recent_readings_for_zone
from app.crud.crud_zone import (
    create_zone,
    get_zone,
    get_zones,
    update_zone,
)
from app.models.user import User
from app.schemas.zone import (
    ZoneCreate,
    ZoneOut,
    ZoneRiskSummary,
    ZoneUpdate,
)
from app.services.risk_service import COLOR_MAP, calculate_zone_risk

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("", response_model=List[ZoneOut])
def list_zones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_zones(db, skip=skip, limit=limit)


@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def add_zone(
    zone_in: ZoneCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    return create_zone(db, zone_in)


@router.get("/{zone_id}", response_model=ZoneOut)
def read_zone(zone_id: UUID, db: Session = Depends(get_db)):
    zone = get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone


@router.patch("/{zone_id}", response_model=ZoneOut)
def modify_zone(
    zone_id: UUID,
    zone_in: ZoneUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    zone = get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return update_zone(db, zone, zone_in)


@router.get("/{zone_id}/current-risk", response_model=ZoneRiskSummary)
def get_zone_current_risk(zone_id: UUID, db: Session = Depends(get_db)):
    zone = get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

    risk = get_latest_risk_for_zone(db, zone_id)
    if not risk:
        # Calculate on the fly if no assessment exists yet
        risk = calculate_zone_risk(db, zone)

    recent_readings = get_recent_readings_for_zone(db, zone.id, hours=24)
    rainfall_24h = sum(r.precipitation_mm for r in recent_readings) if recent_readings else 0.0
    latest_weather = get_latest_reading_for_zone(db, zone.id)
    forecast_24h = latest_weather.forecast_precipitation_24h_mm if latest_weather and latest_weather.forecast_precipitation_24h_mm else 0.0

    active_incidents = get_incidents(db, zone_id=zone.id, limit=200)
    active_count = len([i for i in active_incidents if i.status in ["submitted", "verified", "in_progress"]])

    return ZoneRiskSummary(
        id=zone.id,
        name=zone.name,
        district=zone.district,
        latitude=zone.latitude,
        longitude=zone.longitude,
        current_risk_level=risk.risk_level,
        risk_color=COLOR_MAP.get(risk.risk_level, "#22c55e"),
        risk_score=risk.risk_score,
        primary_risk_type=risk.risk_type,
        recent_rainfall_24h_mm=round(rainfall_24h, 2),
        forecast_rainfall_24h_mm=round(forecast_24h, 2),
        active_incident_count=active_count,
        last_updated=risk.assessed_at,
        boundary_geojson=zone.boundary_geojson,
    )
