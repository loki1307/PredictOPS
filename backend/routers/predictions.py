"""
routers/predictions.py — On-demand ML prediction endpoint.

GET /predictions/{server_id}   Return the latest stored ML scores for a server.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone

from database import get_db
from models import Metric
from schemas import PredictionOut

router = APIRouter(prefix="/predictions", tags=["Predictions"])


def _risk_level(prob: float) -> str:
    if prob >= 0.70: return "CRITICAL"
    if prob >= 0.45: return "HIGH"
    if prob >= 0.20: return "MEDIUM"
    return "LOW"


@router.get("/{server_id}", response_model=PredictionOut)
def get_prediction(server_id: str, db: Session = Depends(get_db)):
    """
    Return the most recently stored ML prediction for the given server.
    The prediction is populated during metric ingestion so this endpoint
    is lightweight (just a DB lookup).
    """
    latest = (
        db.query(Metric)
        .filter(Metric.server_id == server_id)
        .order_by(desc(Metric.timestamp))
        .first()
    )

    if not latest:
        raise HTTPException(status_code=404, detail=f"No data found for server '{server_id}'")

    return PredictionOut(
        server_id     = server_id,
        anomaly_score = latest.anomaly_score or 0.0,
        failure_prob  = latest.failure_prob  or 0.0,
        risk_level    = _risk_level(latest.failure_prob or 0.0),
        timestamp     = latest.timestamp,
    )
