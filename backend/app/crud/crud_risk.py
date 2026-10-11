from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.risk import RiskAssessment
from app.schemas.risk import RiskAssessmentCreate


def get_latest_risk_for_zone(db: Session, zone_id: UUID) -> Optional[RiskAssessment]:
    return (
        db.query(RiskAssessment)
        .filter(RiskAssessment.zone_id == zone_id)
        .order_by(desc(RiskAssessment.assessed_at))
        .first()
    )


def create_risk_assessment(db: Session, assessment_in: RiskAssessmentCreate) -> RiskAssessment:
    assessment = RiskAssessment(**assessment_in.model_dump())
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def get_risk_history(
    db: Session,
    zone_id: Optional[UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 100,
) -> List[RiskAssessment]:
    query = db.query(RiskAssessment)
    if zone_id:
        query = query.filter(RiskAssessment.zone_id == zone_id)
    if from_date:
        query = query.filter(RiskAssessment.assessed_at >= from_date)
    if to_date:
        query = query.filter(RiskAssessment.assessed_at <= to_date)
    return query.order_by(desc(RiskAssessment.assessed_at)).limit(limit).all()
