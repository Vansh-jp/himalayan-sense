from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class WeatherReadingBase(BaseModel):
    zone_id: UUID
    timestamp: datetime
    precipitation_mm: float = Field(..., ge=0.0)
    temperature_c: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    forecast_precipitation_24h_mm: Optional[float] = Field(0.0, ge=0.0)
    source: str = "open-meteo"


class WeatherReadingCreate(WeatherReadingBase):
    pass


class WeatherReadingOut(WeatherReadingBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class WeatherCurrentOut(BaseModel):
    zone_id: UUID
    zone_name: str
    latitude: float
    longitude: float
    current_temperature_c: Optional[float]
    current_precipitation_mm: float
    current_humidity: Optional[float]
    current_wind_speed: Optional[float]
    rainfall_last_24h_mm: float
    forecast_next_24h_mm: float
    timestamp: datetime
    source: str


class WeatherHourlyPoint(BaseModel):
    time: str
    precipitation_mm: float
    temperature_c: Optional[float] = None
    humidity: Optional[float] = None


class WeatherForecastOut(BaseModel):
    zone_id: UUID
    zone_name: str
    latitude: float
    longitude: float
    forecast_next_24h_mm: float
    forecast_next_48h_mm: float
    forecast_next_72h_mm: float
    hourly: List[WeatherHourlyPoint]


class WeatherIngestResponse(BaseModel):
    status: str
    readings_created: int
    zones_updated: int
    errors: List[str] = []
