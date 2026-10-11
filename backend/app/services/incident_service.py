from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Optional
import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.crud.crud_incident import (
    create_incident,
    get_incident,
    update_incident_status,
)
from app.crud.crud_zone import find_zone_for_coordinates, get_zone
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentUpdateStatus
from app.services.alert_service import create_incident_alert_if_needed


def save_uploaded_photo(file: UploadFile) -> str:
    """Save citizen report photo locally in uploads directory."""
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    extension = os.path.splitext(file.filename or "")[1].lower()
    if not extension or extension not in [".jpg", ".jpeg", ".png", ".webp"]:
        extension = ".jpg"

    unique_filename = f"incident_{uuid.uuid4().hex}{extension}"
    target_file = upload_path / unique_filename

    with open(target_file, "wb") as buffer:
        buffer.write(file.file.read())

    return f"/uploads/{unique_filename}"


def submit_citizen_incident(
    db: Session,
    incident_in: IncidentCreate,
    current_user: User,
) -> Incident:
    # Auto-detect zone if not explicitly set
    if not incident_in.zone_id:
        matched_zone = find_zone_for_coordinates(db, incident_in.latitude, incident_in.longitude)
        if matched_zone:
            incident_in.zone_id = matched_zone.id

    incident = create_incident(db, incident_in, user_id=current_user.id)
    return incident


def update_status_by_admin(
    db: Session,
    incident_id: uuid.UUID,
    status_update: IncidentUpdateStatus,
) -> Optional[Incident]:
    incident = get_incident(db, incident_id)
    if not incident:
        return None

    prev_status = incident.status
    updated = update_incident_status(
        db,
        incident,
        status=status_update.status,
        admin_note=status_update.admin_note,
    )

    # If verified, trigger alert check if high severity
    if updated.status == "verified" and updated.zone_id:
        zone = get_zone(db, updated.zone_id)
        if zone:
            create_incident_alert_if_needed(db, zone, updated)
            # Re-evaluate zone risk in background
            try:
                from app.services.risk_service import calculate_zone_risk
                calculate_zone_risk(db, zone)
            except Exception:
                pass

    return updated
