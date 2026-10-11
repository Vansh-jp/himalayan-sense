from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(Uuid, ForeignKey("zones.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # landslide | flood | road_block | unsafe_route | other
    description = Column(Text, nullable=False)
    photo_url = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    landmark = Column(String(255), nullable=True)
    severity = Column(String(20), default="medium", nullable=False)  # low | medium | high
    status = Column(String(30), default="submitted", nullable=False, index=True)  # submitted | verified | in_progress | resolved | rejected
    admin_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="incidents")
    zone = relationship("Zone", back_populates="incidents")
    alerts = relationship("Alert", back_populates="incident")
