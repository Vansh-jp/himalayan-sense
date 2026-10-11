from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    zone_id = Column(Uuid, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_assessment_id = Column(Uuid, ForeignKey("risk_assessments.id", ondelete="SET NULL"), nullable=True)
    incident_id = Column(Uuid, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)  # yellow | orange | red
    channel = Column(String(30), default="in_app", nullable=False)  # in_app | email | sms | whatsapp
    status = Column(String(30), default="sent", nullable=False)  # created | sent | failed
    sent_at = Column(DateTime(timezone=True), default=utc_now, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    zone = relationship("Zone", back_populates="alerts")
    risk_assessment = relationship("RiskAssessment", back_populates="alerts")
    incident = relationship("Incident", back_populates="alerts")
