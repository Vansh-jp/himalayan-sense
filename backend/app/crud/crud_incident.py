from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.crud.crud_zone import haversine_distance
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate


def get_incident(db: Session, incident_id: UUID) -> Optional[Incident]:
    return db.query(Incident).filter(Incident.id == incident_id).first()


def get_incidents(
    db: Session,
    status: Optional[str] = None,
    category: Optional[str] = None,
    zone_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    user_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Incident]:
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if category:
        query = query.filter(Incident.category == category)
    if zone_id:
        query = query.filter(Incident.zone_id == zone_id)
    if severity:
        query = query.filter(Incident.severity == severity)
    if user_id:
        query = query.filter(Incident.user_id == user_id)
    return query.order_by(desc(Incident.created_at)).offset(skip).limit(limit).all()


def create_incident(
    db: Session,
    incident_in: IncidentCreate,
    user_id: UUID,
) -> Incident:
    data = incident_in.model_dump()
    incident = Incident(
        user_id=user_id,
        **data,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def update_incident_status(
    db: Session,
    db_incident: Incident,
    status: str,
    admin_note: Optional[str] = None,
) -> Incident:
    db_incident.status = status
    if admin_note is not None:
        db_incident.admin_note = admin_note
    if status == "resolved":
        db_incident.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_incident)
    return db_incident


def get_nearby_incidents(
    db: Session,
    lat: float,
    lon: float,
    radius_km: float = 10.0,
    limit: int = 50,
) -> List[Tuple[Incident, float]]:
    all_incidents = db.query(Incident).all()
    results = []
    for inc in all_incidents:
        dist = haversine_distance(lat, lon, inc.latitude, inc.longitude)
        if dist <= radius_km:
            results.append((inc, round(dist, 2)))
    results.sort(key=lambda x: x[1])
    return results[:limit]
