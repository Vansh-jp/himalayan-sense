from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class AlertBase(BaseModel):
    zone_id: UUID
    title: str = Field(..., max_length=255)
    message: str
    risk_level: str = Field(..., pattern="^(yellow|orange|red)$")
    channel: str = Field("in_app", pattern="^(in_app|email|sms|whatsapp)$")
    risk_assessment_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None


class AlertCreate(AlertBase):
    status: str = "sent"


class AlertZoneSummary(BaseModel):
    id: UUID
    name: str
    district: str

    class Config:
        from_attributes = True


class AlertOut(AlertBase):
    id: UUID
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime
    zone: Optional[AlertZoneSummary] = None

    class Config:
        from_attributes = True


class AlertSubscribeRequest(BaseModel):
    zone_id: Optional[UUID] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    channels: list[str] = ["in_app", "email"]
