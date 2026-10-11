from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class RiskAssessmentBase(BaseModel):
    zone_id: UUID
    risk_type: str = Field("combined", pattern="^(landslide|flood|road_block|combined)$")
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str = Field(..., pattern="^(green|yellow|orange|red)$")
    model_version: str = "rule_v1"
    explanation: Dict[str, Any]


class RiskAssessmentCreate(RiskAssessmentBase):
    pass


class RiskAssessmentOut(RiskAssessmentBase):
    id: UUID
    assessed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class RiskMapFeature(BaseModel):
    zone_id: UUID
    name: str
    district: str
    risk_level: str  # green, yellow, orange, red
    risk_color: str  # hex color code
    risk_score: float
    primary_risk_type: str
    rainfall_last_24h_mm: float
    forecast_rainfall_24h_mm: float
    active_incidents: int
    last_updated: datetime
    explanation_summary: str
    boundary_geojson: Dict[str, Any]


class RiskMapResponse(BaseModel):
    count: int
    timestamp: datetime
    features: List[RiskMapFeature]


class RiskRecalculateResponse(BaseModel):
    status: str
    zones_evaluated: int
    assessments_created: int
    alerts_generated: int
    timestamp: datetime
