from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.schemas.alert import AlertCreate


def get_alert(db: Session, alert_id: UUID) -> Optional[Alert]:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def get_alerts(
    db: Session,
    zone_id: Optional[UUID] = None,
    risk_level: Optional[str] = None,
    channel: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Alert]:
    query = db.query(Alert)
    if zone_id:
        query = query.filter(Alert.zone_id == zone_id)
    if risk_level:
        query = query.filter(Alert.risk_level == risk_level)
    if channel:
        query = query.filter(Alert.channel == channel)
    return query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()


def create_alert(db: Session, alert_in: AlertCreate) -> Alert:
    alert = Alert(**alert_in.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_recent_alert_for_zone(
    db: Session,
    zone_id: UUID,
    hours: int = 6,
) -> Optional[Alert]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        db.query(Alert)
        .filter(Alert.zone_id == zone_id, Alert.created_at >= since)
        .order_by(desc(Alert.created_at))
        .first()
    )
