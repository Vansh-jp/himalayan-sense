import uuid
from sqlalchemy import Column, Float, Integer, JSON, String, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Zone(Base, TimestampMixin):
    __tablename__ = "zones"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    district = Column(String(100), default="Dehradun", nullable=False)
    state = Column(String(100), default="Uttarakhand", nullable=False)
    zone_type = Column(String(50), default="ward", nullable=False)  # ward | route | village
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    boundary_geojson = Column(JSON, nullable=False)
    terrain_susceptibility_score = Column(Float, default=0.5, nullable=False)  # 0.0 to 1.0
    historical_incident_count = Column(Integer, default=0, nullable=False)

    # Relationships
    weather_readings = relationship("WeatherReading", back_populates="zone", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="zone", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="zone")
    alerts = relationship("Alert", back_populates="zone", cascade="all, delete-orphan")
