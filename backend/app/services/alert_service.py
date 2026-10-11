from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.config import settings
from app.crud.crud_alert import (
    create_alert,
    get_alerts,
    get_recent_alert_for_zone,
)
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.risk import RiskAssessment
from app.models.zone import Zone
from app.schemas.alert import AlertCreate

logger = logging.getLogger(__name__)

LEVEL_SEVERITY_ORDER = {
    "green": 0,
    "yellow": 1,
    "orange": 2,
    "red": 3,
}


def send_smtp_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send SMTP email alert if configured, otherwise skip gracefully."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.debug("SMTP not configured. Skipping external email dispatch.")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.ALERT_FROM_EMAIL
        msg["To"] = to_email
        part = MIMEText(html_body, "html")
        msg.attach(part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.ALERT_FROM_EMAIL, [to_email], msg.as_string())
        logger.info(f"Alert email sent to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send SMTP email: {exc}")
        return False


def should_send_zone_alert(db: Session, zone_id: UUID, new_level: str) -> bool:
    """Deduplication rule:
    - Do not send alert for Green level.
    - Do not send same alert to same zone within 6 hours.
    - Send only if risk level escalated or >= 6 hours passed.
    """
    if new_level not in ["orange", "red", "yellow"]:
        return False

    recent = get_recent_alert_for_zone(db, zone_id, hours=6)
    if not recent:
        return True

    recent_order = LEVEL_SEVERITY_ORDER.get(recent.risk_level.lower(), 0)
    new_order = LEVEL_SEVERITY_ORDER.get(new_level.lower(), 0)

    # Allow alert if risk level increased
    if new_order > recent_order:
        return True

    return False


def create_risk_alert_if_needed(
    db: Session,
    zone: Zone,
    risk: RiskAssessment,
) -> Optional[Alert]:
    if risk.risk_level not in ["orange", "red"]:
        return None

    if not should_send_zone_alert(db, zone.id, risk.risk_level):
        return None

    level_display = "High Landslide Risk" if risk.risk_level == "orange" else "Severe Disaster Emergency"
    title = f"{level_display} Alert — {zone.name}, {zone.district}"
    
    explanation_notes = risk.explanation.get("override_reasons", []) if isinstance(risk.explanation, dict) else []
    reason_str = " Heavy rainfall and critical terrain susceptibility detected."
    if explanation_notes:
        reason_str = f" {explanation_notes[0]}"

    message = (
        f"{title}\n"
        f"A risk score of {risk.risk_score:.1f}/100 has been assessed for {zone.name}."
        f"{reason_str}\n"
        f"Residents and commuters: Avoid steep slopes, vulnerable road cuts, and swollen riverbanks. "
        f"Report incidents via HimalayaSense."
    )

    alert_in = AlertCreate(
        zone_id=zone.id,
        risk_assessment_id=risk.id,
        incident_id=None,
        title=title,
        message=message,
        risk_level=risk.risk_level,
        channel="in_app",
        status="sent",
    )
    alert = create_alert(db, alert_in)

    # Attempt email broadcast if recipient list exists
    if settings.SMTP_USER:
        send_smtp_email(
            to_email=settings.SMTP_USER,
            subject=f"[HimalayaSense ALERT] {title}",
            html_body=f"<div style='font-family:sans-serif;'><h2>{title}</h2><p>{message}</p></div>",
        )

    return alert


def create_incident_alert_if_needed(
    db: Session,
    zone: Zone,
    incident: Incident,
) -> Optional[Alert]:
    """Create alert when a high-severity incident is verified."""
    if incident.severity != "high" or incident.status != "verified":
        return None

    title = f"High Incident Alert: {incident.category.replace('_', ' ').title()} in {zone.name}"
    message = (
        f"A verified high-severity {incident.category.replace('_', ' ')} has been reported near "
        f"{incident.landmark or zone.name}. Details: {incident.description}. Use caution."
    )

    alert_in = AlertCreate(
        zone_id=zone.id,
        incident_id=incident.id,
        title=title,
        message=message,
        risk_level="orange",
        channel="in_app",
        status="sent",
    )
    return create_alert(db, alert_in)
