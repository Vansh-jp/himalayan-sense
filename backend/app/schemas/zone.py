from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ZoneBase(BaseModel):
    name: str = Field(..., max_length=150)
    district: str = Field("Dehradun", max_length=100)
    state: str = Field("Uttarakhand", max_length=100)
    zone_type: str = Field("ward", pattern="^(ward|route|village)$")
    latitude: float
    longitude: float
    boundary_geojson: Dict[str, Any]
    terrain_susceptibility_score: float = Field(0.5, ge=0.0, le=1.0)
    historical_incident_count: int = Field(0, ge=0)


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    zone_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    boundary_geojson: Optional[Dict[str, Any]] = None
    terrain_susceptibility_score: Optional[float] = None
    historical_incident_count: Optional[int] = None


class ZoneOut(ZoneBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ZoneRiskSummary(BaseModel):
    id: UUID
    name: str
    district: str
    latitude: float
    longitude: float
    current_risk_level: str  # green | yellow | orange | red
    risk_color: str
    risk_score: float
    primary_risk_type: str
    recent_rainfall_24h_mm: float
    forecast_rainfall_24h_mm: float
    active_incident_count: int
    last_updated: datetime
    boundary_geojson: Dict[str, Any]
