"""
routers/alerts.py — Alert retrieval and acknowledgement endpoints.

GET  /alerts                  Return recent alert history.
POST /alerts/{id}/acknowledge Mark an alert as acknowledged.
GET  /alerts/stats            Return alert counts by severity.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List

from database import get_db
from models import Alert
from schemas import AlertOut, AcknowledgeIn

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertOut])
def get_alerts(
    limit: int = Query(default=50, le=200),
    server_id: str = Query(default=None),
    severity: str = Query(default=None),
    unacknowledged_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """
    Return alert history, optionally filtered by server, severity, or acknowledgement status.
    """
    q = db.query(Alert)

    if server_id:
        q = q.filter(Alert.server_id == server_id)
    if severity:
        q = q.filter(Alert.severity == severity.upper())
    if unacknowledged_only:
        q = q.filter(Alert.acknowledged == False)

    return q.order_by(desc(Alert.timestamp)).limit(limit).all()


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: int,
    body: AcknowledgeIn,
    db: Session = Depends(get_db),
):
    """Acknowledge (or un-acknowledge) an alert by ID."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    alert.acknowledged = body.acknowledged
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/stats/summary")
def get_alert_stats(db: Session = Depends(get_db)):
    """Return counts of alerts grouped by severity."""
    rows = (
        db.query(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity)
        .all()
    )
    return {severity: count for severity, count in rows}
