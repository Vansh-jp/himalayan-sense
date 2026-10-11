from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.crud.crud_weather import (
    create_weather_readings_batch,
    get_latest_reading_for_zone,
    get_recent_readings_for_zone,
)
from app.crud.crud_zone import get_zone, get_zones
from app.models.zone import Zone
from app.schemas.weather import (
    WeatherCurrentOut,
    WeatherForecastOut,
    WeatherHourlyPoint,
    WeatherReadingCreate,
)

logger = logging.getLogger(__name__)


def fetch_open_meteo_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 3,
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """Fetch hourly weather from Open-Meteo with retries."""
    url = f"{settings.OPEN_METEO_BASE_URL.rstrip('/')}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "precipitation,temperature_2m,relative_humidity_2m,wind_speed_10m",
        "forecast_days": forecast_days,
        "timezone": "Asia/Kolkata",
    }

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                logger.warning(
                    f"Open-Meteo attempt {attempt}/{max_retries} returned status {response.status_code}: {response.text}"
                )
        except Exception as exc:
            logger.warning(f"Open-Meteo attempt {attempt}/{max_retries} failed: {exc}")

        if attempt < max_retries:
            time.sleep(1.0 * attempt)

    logger.error(f"Failed to fetch Open-Meteo weather for ({latitude}, {longitude}) after {max_retries} attempts")
    return None


def ingest_weather_for_zone(db: Session, zone: Zone) -> int:
    """Fetch Open-Meteo data for a single zone and store hourly records."""
    data = fetch_open_meteo_forecast(zone.latitude, zone.longitude, forecast_days=3)
    if not data or "hourly" not in data:
        logger.warning(f"Could not ingest live weather for zone {zone.name}, fallback to existing")
        return 0

    hourly = data["hourly"]
    times = hourly.get("time", [])
    precips = hourly.get("precipitation", [])
    temps = hourly.get("temperature_2m", [])
    hums = hourly.get("relative_humidity_2m", [])
    winds = hourly.get("wind_speed_10m", [])

    # Calculate forecast sum for next 24h
    next_24h_sum = sum(precips[:24]) if len(precips) >= 24 else sum(precips)

    readings_to_create: List[WeatherReadingCreate] = []
    # Save the most recent and upcoming 24 hours of hourly forecasts
    limit = min(len(times), 24)
    for i in range(limit):
        try:
            # Parse ISO timestamp from Open-Meteo (e.g. 2026-10-11T12:00)
            t_str = times[i]
            dt = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
            reading = WeatherReadingCreate(
                zone_id=zone.id,
                timestamp=dt,
                precipitation_mm=float(precips[i] if precips[i] is not None else 0.0),
                temperature_c=float(temps[i]) if i < len(temps) and temps[i] is not None else None,
                humidity=float(hums[i]) if i < len(hums) and hums[i] is not None else None,
                wind_speed=float(winds[i]) if i < len(winds) and winds[i] is not None else None,
                forecast_precipitation_24h_mm=round(float(next_24h_sum), 2),
                source="open-meteo",
            )
            readings_to_create.append(reading)
        except Exception as e:
            logger.debug(f"Error parsing weather point: {e}")

    if readings_to_create:
        return create_weather_readings_batch(db, readings_to_create)
    return 0


def ingest_weather_for_all_zones(db: Session) -> Dict[str, Any]:
    zones = get_zones(db, limit=200)
    created_total = 0
    updated_zones = 0
    errors = []

    for zone in zones:
        try:
            count = ingest_weather_for_zone(db, zone)
            if count > 0:
                created_total += count
                updated_zones += 1
        except Exception as e:
            errors.append(f"Zone {zone.name}: {str(e)}")

    return {
        "status": "success" if not errors else "partial_success",
        "readings_created": created_total,
        "zones_updated": updated_zones,
        "errors": errors,
    }


def get_current_weather(db: Session, zone_id: UUID) -> Optional[WeatherCurrentOut]:
    zone = get_zone(db, zone_id)
    if not zone:
        return None

    latest = get_latest_reading_for_zone(db, zone_id)
    recent = get_recent_readings_for_zone(db, zone_id, hours=24)
    precip_24h = sum(r.precipitation_mm for r in recent) if recent else 0.0

    if latest:
        return WeatherCurrentOut(
            zone_id=zone.id,
            zone_name=zone.name,
            latitude=zone.latitude,
            longitude=zone.longitude,
            current_temperature_c=latest.temperature_c,
            current_precipitation_mm=latest.precipitation_mm,
            current_humidity=latest.humidity,
            current_wind_speed=latest.wind_speed,
            rainfall_last_24h_mm=round(precip_24h, 2),
            forecast_next_24h_mm=latest.forecast_precipitation_24h_mm or 0.0,
            timestamp=latest.timestamp,
            source=latest.source,
        )

    # Fallback default if no readings stored yet
    return WeatherCurrentOut(
        zone_id=zone.id,
        zone_name=zone.name,
        latitude=zone.latitude,
        longitude=zone.longitude,
        current_temperature_c=22.0,
        current_precipitation_mm=0.0,
        current_humidity=65.0,
        current_wind_speed=5.0,
        rainfall_last_24h_mm=0.0,
        forecast_next_24h_mm=5.0,
        timestamp=datetime.now(timezone.utc),
        source="default_estimate",
    )


def get_forecast_weather(db: Session, zone_id: UUID) -> Optional[WeatherForecastOut]:
    zone = get_zone(db, zone_id)
    if not zone:
        return None

    # Try live fetch from Open-Meteo
    live_data = fetch_open_meteo_forecast(zone.latitude, zone.longitude, forecast_days=3)
    if live_data and "hourly" in live_data:
        h = live_data["hourly"]
        times = h.get("time", [])
        precips = h.get("precipitation", [])
        temps = h.get("temperature_2m", [])
        hums = h.get("relative_humidity_2m", [])

        points: List[WeatherHourlyPoint] = []
        for i in range(min(len(times), 72)):
            points.append(
                WeatherHourlyPoint(
                    time=times[i],
                    precipitation_mm=float(precips[i] if precips[i] is not None else 0.0),
                    temperature_c=float(temps[i]) if i < len(temps) and temps[i] is not None else None,
                    humidity=float(hums[i]) if i < len(hums) and hums[i] is not None else None,
                )
            )

        f_24 = sum(p.precipitation_mm for p in points[:24])
        f_48 = sum(p.precipitation_mm for p in points[:48])
        f_72 = sum(p.precipitation_mm for p in points[:72])

        return WeatherForecastOut(
            zone_id=zone.id,
            zone_name=zone.name,
            latitude=zone.latitude,
            longitude=zone.longitude,
            forecast_next_24h_mm=round(f_24, 2),
            forecast_next_48h_mm=round(f_48, 2),
            forecast_next_72h_mm=round(f_72, 2),
            hourly=points,
        )

    # Fallback to stored database readings
    recent = get_recent_readings_for_zone(db, zone_id, hours=24)
    latest = get_latest_reading_for_zone(db, zone_id)
    f24 = latest.forecast_precipitation_24h_mm if latest and latest.forecast_precipitation_24h_mm else 0.0
    return WeatherForecastOut(
        zone_id=zone.id,
        zone_name=zone.name,
        latitude=zone.latitude,
        longitude=zone.longitude,
        forecast_next_24h_mm=f24,
        forecast_next_48h_mm=round(f24 * 1.8, 2),
        forecast_next_72h_mm=round(f24 * 2.5, 2),
        hourly=[],
    )
