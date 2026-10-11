from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WeatherReading(Base):
    __tablename__ = "weather_readings"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    zone_id = Column(Uuid, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    precipitation_mm = Column(Float, nullable=False, default=0.0)
    temperature_c = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    forecast_precipitation_24h_mm = Column(Float, nullable=True, default=0.0)
    source = Column(String(50), default="open-meteo", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    zone = relationship("Zone", back_populates="weather_readings")
