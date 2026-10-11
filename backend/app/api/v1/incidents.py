from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.crud.crud_incident import (
    get_incident,
    get_incidents,
    get_nearby_incidents,
)
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import (
    IncidentCreate,
    IncidentNearbyItem,
    IncidentOut,
    IncidentUpdateStatus,
)
from app.services.incident_service import (
    save_uploaded_photo,
    submit_citizen_incident,
    update_status_by_admin,
)

router = APIRouter(prefix="/incidents", tags=["Citizen Incidents"])


@router.post("/upload", response_model=dict)
def upload_incident_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload an incident photograph to local storage."""
    url = save_uploaded_photo(file)
    return {"photo_url": url, "filename": file.filename}


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def report_incident(
    incident_in: IncidentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Citizen creates incident report with GPS coordinates and optional photo."""
    return submit_citizen_incident(db, incident_in, current_user)


@router.get("", response_model=List[IncidentOut])
def list_incidents(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    zone_id: Optional[UUID] = Query(None),
    severity: Optional[str] = Query(None),
    user_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return get_incidents(
        db,
        status=status,
        category=category,
        zone_id=zone_id,
        severity=severity,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )


@router.get("/nearby", response_model=List[IncidentNearbyItem])
def find_nearby_incidents(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(10.0, ge=0.5, le=100.0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    results = get_nearby_incidents(db, lat=latitude, lon=longitude, radius_km=radius_km, limit=limit)
    out: List[IncidentNearbyItem] = []
    for inc, dist in results:
        item = IncidentNearbyItem(
            id=inc.id,
            user_id=inc.user_id,
            zone_id=inc.zone_id,
            category=inc.category,
            description=inc.description,
            photo_url=inc.photo_url,
            latitude=inc.latitude,
            longitude=inc.longitude,
            landmark=inc.landmark,
            severity=inc.severity,
            status=inc.status,
            admin_note=inc.admin_note,
            created_at=inc.created_at,
            updated_at=inc.updated_at,
            resolved_at=inc.resolved_at,
            user=inc.user,
            zone=inc.zone,
            distance_km=dist,
        )
        out.append(item)
    return out


@router.get("/{incident_id}", response_model=IncidentOut)
def read_incident(incident_id: UUID, db: Session = Depends(get_db)):
    inc = get_incident(db, incident_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return inc


@router.patch("/{incident_id}/status", response_model=IncidentOut)
def change_incident_status(
    incident_id: UUID,
    status_update: IncidentUpdateStatus,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Authority/Admin workflow transition: submitted -> verified -> in_progress -> resolved / rejected."""
    updated = update_status_by_admin(db, incident_id, status_update)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return updated
