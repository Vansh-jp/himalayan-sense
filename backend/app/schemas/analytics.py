from typing import Dict, List, Optional
from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_incidents: int
    pending_verification: int
    active_incidents: int
    resolved_incidents: int
    rejected_incidents: int
    avg_resolution_time_hours: Optional[float] = 0.0
    total_zones: int
    high_or_severe_risk_zones: int
    total_alerts_24h: int


class IncidentsByCategoryItem(BaseModel):
    category: str
    count: int


class IncidentsByZoneItem(BaseModel):
    zone_name: str
    count: int


class IncidentsTimelinePoint(BaseModel):
    date: str
    count: int


class AnalyticsIncidents(BaseModel):
    by_category: List[IncidentsByCategoryItem]
    by_zone: List[IncidentsByZoneItem]
    by_status: Dict[str, int]
    timeline_7d: List[IncidentsTimelinePoint]


class RiskDistributionItem(BaseModel):
    level: str
    count: int
    color: str


class ZoneRiskComparisonItem(BaseModel):
    zone_name: str
    risk_level: str
    risk_score: float
    rainfall_24h_mm: float
    active_incidents: int


class RainfallVsIncidentPoint(BaseModel):
    zone_name: str
    rainfall_24h_mm: float
    incident_count: int


class AnalyticsRisk(BaseModel):
    distribution: List[RiskDistributionItem]
    zones: List[ZoneRiskComparisonItem]
    rainfall_vs_incidents: List[RainfallVsIncidentPoint]


class AlertChannelItem(BaseModel):
    channel: str
    count: int


class AlertLevelItem(BaseModel):
    level: str
    count: int


class AnalyticsAlerts(BaseModel):
    total_alerts: int
    by_level: List[AlertLevelItem]
    by_channel: List[AlertChannelItem]
    recent_alerts: list
