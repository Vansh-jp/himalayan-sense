from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.crud.crud_alert import get_alerts
from app.crud.crud_incident import get_incidents
from app.crud.crud_risk import get_latest_risk_for_zone
from app.crud.crud_weather import get_recent_readings_for_zone
from app.crud.crud_zone import get_zones
from app.models.incident import Incident
from app.models.user import User
from app.schemas.alert import AlertOut
from app.schemas.analytics import (
    AlertChannelItem,
    AlertLevelItem,
    AnalyticsAlerts,
    AnalyticsIncidents,
    AnalyticsOverview,
    AnalyticsRisk,
    IncidentsByCategoryItem,
    IncidentsByZoneItem,
    IncidentsTimelinePoint,
    RainfallVsIncidentPoint,
    RiskDistributionItem,
    ZoneRiskComparisonItem,
)
from app.services.risk_service import COLOR_MAP

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    incidents = db.query(Incident).all()
    zones = get_zones(db, limit=200)

    total_incidents = len(incidents)
    pending = len([i for i in incidents if i.status == "submitted"])
    active = len([i for i in incidents if i.status in ["verified", "in_progress"]])
    resolved = [i for i in incidents if i.status == "resolved" and i.resolved_at]
    rejected = len([i for i in incidents if i.status == "rejected"])

    # Average resolution time in hours
    res_durations = [
        (i.resolved_at.replace(tzinfo=timezone.utc) - i.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600.0
        for i in resolved
        if i.resolved_at and i.created_at
    ]
    avg_hours = round(sum(res_durations) / len(res_durations), 1) if res_durations else 0.0

    high_risk_zones = 0
    for z in zones:
        latest_risk = get_latest_risk_for_zone(db, z.id)
        if latest_risk and latest_risk.risk_level in ["orange", "red"]:
            high_risk_zones += 1

    alerts_24h = len(get_alerts(db, limit=100))

    return AnalyticsOverview(
        total_incidents=total_incidents,
        pending_verification=pending,
        active_incidents=active,
        resolved_incidents=len(resolved),
        rejected_incidents=rejected,
        avg_resolution_time_hours=avg_hours,
        total_zones=len(zones),
        high_or_severe_risk_zones=high_risk_zones,
        total_alerts_24h=alerts_24h,
    )


@router.get("/incidents", response_model=AnalyticsIncidents)
def get_analytics_incidents(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    incidents = db.query(Incident).all()

    # Category counts
    cat_counts = Counter(i.category for i in incidents)
    by_category = [
        IncidentsByCategoryItem(category=c, count=n)
        for c, n in cat_counts.items()
    ]

    # Zone counts
    zone_counts: Counter = Counter()
    for inc in incidents:
        z_name = inc.zone.name if inc.zone else "Unassigned"
        zone_counts[z_name] += 1
    by_zone = [
        IncidentsByZoneItem(zone_name=z, count=n)
        for z, n in zone_counts.items()
    ]

    # Status counts
    by_status = dict(Counter(i.status for i in incidents))

    # 7-day timeline
    now = datetime.now(timezone.utc)
    timeline: List[IncidentsTimelinePoint] = []
    for d in range(6, -1, -1):
        day_date = (now - timedelta(days=d)).date()
        day_str = day_date.strftime("%Y-%m-%d")
        cnt = sum(
            1 for i in incidents
            if i.created_at and i.created_at.date() == day_date
        )
        timeline.append(IncidentsTimelinePoint(date=day_str, count=cnt))

    return AnalyticsIncidents(
        by_category=by_category,
        by_zone=by_zone,
        by_status=by_status,
        timeline_7d=timeline,
    )


@router.get("/risk", response_model=AnalyticsRisk)
def get_analytics_risk(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    zones = get_zones(db, limit=200)

    level_counter = Counter({"green": 0, "yellow": 0, "orange": 0, "red": 0})
    zone_items: List[ZoneRiskComparisonItem] = []
    rainfall_scatter: List[RainfallVsIncidentPoint] = []

    for z in zones:
        risk = get_latest_risk_for_zone(db, z.id)
        lvl = risk.risk_level if risk else "green"
        score = risk.risk_score if risk else 15.0
        level_counter[lvl] += 1

        recent = get_recent_readings_for_zone(db, z.id, hours=24)
        rain_24h = round(sum(r.precipitation_mm for r in recent), 2) if recent else 0.0

        incidents = [i for i in z.incidents if i.status in ["submitted", "verified", "in_progress"]]
        inc_count = len(incidents)

        zone_items.append(
            ZoneRiskComparisonItem(
                zone_name=z.name,
                risk_level=lvl,
                risk_score=score,
                rainfall_24h_mm=rain_24h,
                active_incidents=inc_count,
            )
        )

        rainfall_scatter.append(
            RainfallVsIncidentPoint(
                zone_name=z.name,
                rainfall_24h_mm=rain_24h,
                incident_count=len(z.incidents),
            )
        )

    distribution = [
        RiskDistributionItem(
            level=lvl.capitalize(),
            count=cnt,
            color=COLOR_MAP.get(lvl, "#22c55e"),
        )
        for lvl, cnt in level_counter.items()
    ]

    return AnalyticsRisk(
        distribution=distribution,
        zones=zone_items,
        rainfall_vs_incidents=rainfall_scatter,
    )


@router.get("/alerts", response_model=AnalyticsAlerts)
def get_analytics_alerts(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    alerts = get_alerts(db, limit=200)

    level_counts = Counter(a.risk_level for a in alerts)
    channel_counts = Counter(a.channel for a in alerts)

    by_level = [AlertLevelItem(level=l, count=c) for l, c in level_counts.items()]
    by_channel = [AlertChannelItem(channel=ch, count=c) for ch, c in channel_counts.items()]

    recent_out = [AlertOut.model_validate(a).model_dump() for a in alerts[:15]]

    return AnalyticsAlerts(
        total_alerts=len(alerts),
        by_level=by_level,
        by_channel=by_channel,
        recent_alerts=recent_out,
    )
