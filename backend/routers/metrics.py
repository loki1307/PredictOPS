"""
routers/metrics.py — Metric ingestion and retrieval endpoints.

POST /metrics/ingest   Accept a batch of metric dicts from the simulator.
                       Runs ML inference and stores results.
GET  /metrics/{server_id}   Return recent metric history for a server.
GET  /servers/summary        Return current status of all known servers.
"""

import sys, os

# Add ml/ directory to path so we can import predictor
_ML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml"))
if _ML_DIR not in sys.path:
    sys.path.insert(0, _ML_DIR)

import logging
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import Metric, Alert
from schemas import MetricIn, MetricOut, IngestResponse, PredictionOut, ServerSummary

# Import the singleton ML predictor from ml/predictor.py
try:
    from predictor import predictor
except ImportError:
    predictor = None

log = logging.getLogger("metrics")
router = APIRouter(prefix="/metrics", tags=["Metrics"])


# ---------------------------------------------------------------------------
# Alert deduplication: track last alert time per server
# ---------------------------------------------------------------------------
_last_alert_time: dict = {}   # server_id → datetime
ALERT_COOLDOWN_MINUTES = 5


def _should_alert(server_id: str) -> bool:
    """Return True if enough time has passed since the last alert for this server."""
    last = _last_alert_time.get(server_id)
    if last is None:
        return True
    return (datetime.now(timezone.utc) - last).total_seconds() > ALERT_COOLDOWN_MINUTES * 60


def _record_alert(server_id: str, severity: str, message: str,
                  metric: str, value: float, failure_prob: float, db: Session):
    """Insert an alert row and reset the cooldown timer."""
    alert = Alert(
        server_id    = server_id,
        timestamp    = datetime.now(timezone.utc),
        severity     = severity,
        message      = message,
        metric       = metric,
        value        = value,
        failure_prob = failure_prob,
        acknowledged = False,
    )
    db.add(alert)
    _last_alert_time[server_id] = datetime.now(timezone.utc)
    log.warning("Alert [%s] %s — %s", severity, server_id, message)


# ---------------------------------------------------------------------------
# Helper: determine the worst-looking metric for the alert message
# ---------------------------------------------------------------------------
def _worst_metric(metrics: dict) -> tuple:
    """Return (metric_name, value, descriptive_reason)."""
    checks = [
        ("cpu_percent",     metrics.get("cpu_percent", 0),     80, "CPU utilisation is critically high"),
        ("memory_percent",  metrics.get("memory_percent", 0),  85, "Memory pressure is dangerously high"),
        ("disk_io_percent", metrics.get("disk_io_percent", 0), 85, "Disk I/O saturation detected"),
        ("net_latency_ms",  metrics.get("net_latency_ms", 0),  200, "Network latency is severely elevated"),
        ("packet_loss_pct", metrics.get("packet_loss_pct", 0), 5, "Significant packet loss detected"),
    ]
    worst_name, worst_val, _, worst_reason = max(checks, key=lambda c: c[1] / c[2])
    return worst_name, worst_val, worst_reason


# ---------------------------------------------------------------------------
# POST /metrics/ingest
# ---------------------------------------------------------------------------
@router.post("/ingest", response_model=IngestResponse)
def ingest_metrics(batch: List[MetricIn], db: Session = Depends(get_db)):
    """
    Receive a batch of metric samples from the simulator.
    Runs ML inference on each sample and optionally fires alerts.
    """
    stored       = 0
    predictions  = []

    for item in batch:
        ts = item.timestamp or datetime.now(timezone.utc)

        # ── Run ML inference ──────────────────────────────────────────────
        metrics_dict = {
            "cpu_percent":     item.cpu_percent,
            "memory_percent":  item.memory_percent,
            "disk_io_percent": item.disk_io_percent,
            "net_latency_ms":  item.net_latency_ms,
            "packet_loss_pct": item.packet_loss_pct,
        }

        if predictor is not None:
            anomaly_score, failure_prob, risk_level = predictor.predict(item.server_id, metrics_dict)
        else:
            anomaly_score, failure_prob, risk_level = 0.0, 0.0, "LOW"

        # ── Determine server status from ML + raw metrics ─────────────────
        if failure_prob >= 0.70 or item.cpu_percent >= 90:
            status = "critical"
        elif failure_prob >= 0.40 or item.cpu_percent >= 70:
            status = "warning"
        else:
            status = "healthy"

        # ── Persist metric row ────────────────────────────────────────────
        db_metric = Metric(
            server_id       = item.server_id,
            timestamp       = ts,
            status          = status,
            cpu_percent     = item.cpu_percent,
            memory_percent  = item.memory_percent,
            disk_io_percent = item.disk_io_percent,
            net_latency_ms  = item.net_latency_ms,
            packet_loss_pct = item.packet_loss_pct,
            anomaly_score   = anomaly_score,
            failure_prob    = failure_prob,
        )
        db.add(db_metric)
        stored += 1

        # ── Fire alerts ───────────────────────────────────────────────────
        if _should_alert(item.server_id):
            if failure_prob >= 0.70:
                metric_name, metric_val, reason = _worst_metric(metrics_dict)
                _record_alert(
                    server_id    = item.server_id,
                    severity     = "CRITICAL",
                    message      = (
                        f"[{item.server_id}] Failure probability {failure_prob:.0%} in next 15 min. "
                        f"{reason} (current value: {metric_val:.1f})."
                    ),
                    metric       = metric_name,
                    value        = metric_val,
                    failure_prob = failure_prob,
                    db           = db,
                )
            elif anomaly_score < -0.10 and failure_prob >= 0.30:
                metric_name, metric_val, reason = _worst_metric(metrics_dict)
                _record_alert(
                    server_id    = item.server_id,
                    severity     = "WARNING",
                    message      = (
                        f"[{item.server_id}] Anomalous behaviour detected (score={anomaly_score:.3f}). "
                        f"{reason} (current value: {metric_val:.1f})."
                    ),
                    metric       = metric_name,
                    value        = metric_val,
                    failure_prob = failure_prob,
                    db           = db,
                )

        predictions.append(PredictionOut(
            server_id     = item.server_id,
            anomaly_score = anomaly_score,
            failure_prob  = failure_prob,
            risk_level    = risk_level,
            timestamp     = ts,
        ))

    db.commit()
    return IngestResponse(stored=stored, predictions=predictions)


# ---------------------------------------------------------------------------
# GET /metrics/{server_id}
# ---------------------------------------------------------------------------
@router.get("/{server_id}", response_model=List[MetricOut])
def get_metrics(
    server_id: str,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    """Return the most recent `limit` metric records for a given server."""
    rows = (
        db.query(Metric)
        .filter(Metric.server_id == server_id)
        .order_by(desc(Metric.timestamp))
        .limit(limit)
        .all()
    )
    # Return in chronological order so charts render correctly
    return list(reversed(rows))


# ---------------------------------------------------------------------------
# GET /servers/summary
# ---------------------------------------------------------------------------
servers_router = APIRouter(prefix="/servers", tags=["Servers"])


@servers_router.get("/summary", response_model=List[ServerSummary])
def get_servers_summary(db: Session = Depends(get_db)):
    """
    Return the latest status record for every known server.
    Used by the dashboard server grid.
    """
    # Get all distinct server IDs
    server_ids = [row[0] for row in db.query(Metric.server_id).distinct().all()]

    summaries = []
    for sid in server_ids:
        latest = (
            db.query(Metric)
            .filter(Metric.server_id == sid)
            .order_by(desc(Metric.timestamp))
            .first()
        )
        if latest:
            summaries.append(ServerSummary(
                server_id      = sid,
                status         = latest.status,
                failure_prob   = latest.failure_prob   or 0.0,
                anomaly_score  = latest.anomaly_score  or 0.0,
                risk_level     = _risk_level_from_prob(latest.failure_prob or 0.0),
                last_updated   = latest.timestamp,
                cpu_percent    = latest.cpu_percent,
                memory_percent = latest.memory_percent,
                net_latency_ms = latest.net_latency_ms,
            ))
    return summaries


def _risk_level_from_prob(p: float) -> str:
    if p >= 0.70: return "CRITICAL"
    if p >= 0.45: return "HIGH"
    if p >= 0.20: return "MEDIUM"
    return "LOW"
