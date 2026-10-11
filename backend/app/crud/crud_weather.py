from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.weather import WeatherReading
from app.schemas.weather import WeatherReadingCreate


def get_latest_reading_for_zone(db: Session, zone_id: UUID) -> Optional[WeatherReading]:
    return (
        db.query(WeatherReading)
        .filter(WeatherReading.zone_id == zone_id)
        .order_by(desc(WeatherReading.timestamp))
        .first()
    )


def get_recent_readings_for_zone(
    db: Session,
    zone_id: UUID,
    hours: int = 24,
) -> List[WeatherReading]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        db.query(WeatherReading)
        .filter(WeatherReading.zone_id == zone_id, WeatherReading.timestamp >= since)
        .order_by(WeatherReading.timestamp.asc())
        .all()
    )


def create_weather_reading(db: Session, reading_in: WeatherReadingCreate) -> WeatherReading:
    reading = WeatherReading(**reading_in.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def create_weather_readings_batch(
    db: Session,
    readings: List[WeatherReadingCreate],
) -> int:
    objs = [WeatherReading(**r.model_dump()) for r in readings]
    db.add_all(objs)
    db.commit()
    return len(objs)
