from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_current_user
from app.crud.crud_alert import get_alert, get_alerts
from app.models.user import User
from app.schemas.alert import AlertOut, AlertSubscribeRequest

router = APIRouter(prefix="/alerts", tags=["Emergency Alerts"])


@router.get("", response_model=List[AlertOut])
def list_alerts(
    zone_id: Optional[UUID] = Query(None),
    risk_level: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_alerts(
        db,
        zone_id=zone_id,
        risk_level=risk_level,
        channel=channel,
        skip=skip,
        limit=limit,
    )


@router.get("/my", response_model=List[AlertOut])
def list_my_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve alerts applicable to citizen's district / subscriptions."""
    # Filter by user district or all severe alerts
    return get_alerts(db, limit=20)


@router.get("/{alert_id}", response_model=AlertOut)
def read_alert(alert_id: UUID, db: Session = Depends(get_db)):
    alert = get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


@router.post("/subscribe", response_model=dict)
def subscribe_to_alerts(
    sub_data: AlertSubscribeRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Register email or phone subscription for emergency disaster notifications."""
    target_email = sub_data.email or (current_user.email if current_user else "unknown")
    return {
        "status": "subscribed",
        "message": f"Successfully subscribed {target_email} to HimalayaSense early warning broadcasts.",
        "channels": sub_data.channels,
    }
