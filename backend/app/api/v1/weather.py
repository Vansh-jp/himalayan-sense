from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.crud.crud_zone import get_zone, get_zones
from app.models.user import User
from app.schemas.weather import (
    WeatherCurrentOut,
    WeatherForecastOut,
    WeatherIngestResponse,
)
from app.services.weather_service import (
    get_current_weather,
    get_forecast_weather,
    ingest_weather_for_all_zones,
    ingest_weather_for_zone,
)

router = APIRouter(prefix="/weather", tags=["Weather Ingestion"])


@router.get("/current", response_model=WeatherCurrentOut)
def read_current_weather(
    zone_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    if not zone_id:
        zones = get_zones(db, limit=1)
        if not zones:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No zones configured")
        zone_id = zones[0].id

    data = get_current_weather(db, zone_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weather data not found for zone")
    return data


@router.get("/forecast", response_model=WeatherForecastOut)
def read_weather_forecast(
    zone_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    if not zone_id:
        zones = get_zones(db, limit=1)
        if not zones:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No zones configured")
        zone_id = zones[0].id

    data = get_forecast_weather(db, zone_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast data not found for zone")
    return data


@router.post("/ingest", response_model=WeatherIngestResponse)
def trigger_weather_ingestion(
    zone_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Admin triggers live Open-Meteo ingestion."""
    if zone_id:
        zone = get_zone(db, zone_id)
        if not zone:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
        count = ingest_weather_for_zone(db, zone)
        return WeatherIngestResponse(
            status="success",
            readings_created=count,
            zones_updated=1 if count > 0 else 0,
            errors=[],
        )

    result = ingest_weather_for_all_zones(db)
    return WeatherIngestResponse(**result)
