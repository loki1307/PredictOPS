"""
schemas.py — Pydantic request/response schemas for PredictOps API.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Metric schemas
# ---------------------------------------------------------------------------

class MetricIn(BaseModel):
    """Schema for a single metric record posted by the simulator."""
    server_id:       str   = Field(..., example="web-01")
    timestamp:       Optional[datetime] = None
    status:          str   = Field(default="healthy")
    cpu_percent:     float = Field(..., ge=0, le=100)
    memory_percent:  float = Field(..., ge=0, le=100)
    disk_io_percent: float = Field(..., ge=0, le=100)
    net_latency_ms:  float = Field(..., ge=0)
    packet_loss_pct: float = Field(..., ge=0)


class MetricOut(BaseModel):
    """Schema for returning stored metric data to the frontend."""
    id:              int
    server_id:       str
    timestamp:       datetime
    status:          str
    cpu_percent:     float
    memory_percent:  float
    disk_io_percent: float
    net_latency_ms:  float
    packet_loss_pct: float
    anomaly_score:   Optional[float] = None
    failure_prob:    Optional[float] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Prediction schemas
# ---------------------------------------------------------------------------

class PredictionOut(BaseModel):
    """ML prediction results for one server."""
    server_id:      str
    anomaly_score:  float   # Isolation Forest: negative = anomalous
    failure_prob:   float   # LSTM: 0.0–1.0 probability of failure in 15 min
    risk_level:     str     # LOW / MEDIUM / HIGH / CRITICAL
    timestamp:      datetime


# ---------------------------------------------------------------------------
# Alert schemas
# ---------------------------------------------------------------------------

class AlertOut(BaseModel):
    """Alert record returned to the frontend."""
    id:           int
    server_id:    str
    timestamp:    datetime
    severity:     str
    message:      str
    metric:       Optional[str] = None
    value:        Optional[float] = None
    failure_prob: Optional[float] = None
    acknowledged: bool

    model_config = {"from_attributes": True}


class AcknowledgeIn(BaseModel):
    """Request body to acknowledge an alert."""
    acknowledged: bool = True


# ---------------------------------------------------------------------------
# Server summary schemas (for dashboard)
# ---------------------------------------------------------------------------

class ServerSummary(BaseModel):
    """Aggregated current status of one server."""
    server_id:      str
    status:         str
    failure_prob:   float
    anomaly_score:  float
    risk_level:     str
    last_updated:   Optional[datetime] = None
    cpu_percent:    float
    memory_percent: float
    net_latency_ms: float


class IngestResponse(BaseModel):
    """Response returned after a successful metric ingest."""
    stored:     int
    predictions: List[PredictionOut]
