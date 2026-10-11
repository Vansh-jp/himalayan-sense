from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    zone_id = Column(Uuid, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    assessed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    risk_type = Column(String(50), default="combined", nullable=False)  # landslide | flood | road_block | combined
    risk_score = Column(Float, nullable=False)  # 0.0 - 100.0
    risk_level = Column(String(20), nullable=False, index=True)  # green | yellow | orange | red
    model_version = Column(String(50), default="rule_v1", nullable=False)
    explanation = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    zone = relationship("Zone", back_populates="risk_assessments")
    alerts = relationship("Alert", back_populates="risk_assessment")
