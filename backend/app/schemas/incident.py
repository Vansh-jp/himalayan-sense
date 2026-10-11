from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class IncidentBase(BaseModel):
    category: str = Field(..., pattern="^(landslide|flood|road_block|unsafe_route|other)$")
    description: str = Field(..., min_length=5)
    latitude: float
    longitude: float
    landmark: Optional[str] = Field(None, max_length=255)
    severity: str = Field("medium", pattern="^(low|medium|high)$")
    photo_url: Optional[str] = None
    zone_id: Optional[UUID] = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(submitted|verified|in_progress|resolved|rejected)$")
    admin_note: Optional[str] = None


class IncidentUserSummary(BaseModel):
    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True


class IncidentZoneSummary(BaseModel):
    id: UUID
    name: str
    district: str

    class Config:
        from_attributes = True


class IncidentOut(IncidentBase):
    id: UUID
    user_id: UUID
    status: str
    admin_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    user: Optional[IncidentUserSummary] = None
    zone: Optional[IncidentZoneSummary] = None

    class Config:
        from_attributes = True


class IncidentNearbyItem(IncidentOut):
    distance_km: float
