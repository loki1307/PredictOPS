"""
models.py — SQLAlchemy ORM models for PredictOps.

Tables:
  metrics  — time-series metric snapshots from servers
  alerts   — triggered alert events with severity and status
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)


class Metric(Base):
    """
    One row = one metric sample from one server at one timestamp.
    The simulator posts batches; each row in the batch becomes a Metric row.
    """
    __tablename__ = "metrics"

    id              = Column(Integer, primary_key=True, index=True)
    server_id       = Column(String(50), nullable=False, index=True)
    timestamp       = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status          = Column(String(20), nullable=False, default="healthy")  # healthy/warning/critical

    # Raw system metrics
    cpu_percent     = Column(Float, nullable=False)
    memory_percent  = Column(Float, nullable=False)
    disk_io_percent = Column(Float, nullable=False)
    net_latency_ms  = Column(Float, nullable=False)
    packet_loss_pct = Column(Float, nullable=False)

    # ML outputs (populated by the prediction engine after ingestion)
    anomaly_score   = Column(Float, nullable=True)    # Isolation Forest score (<0 = anomaly)
    failure_prob    = Column(Float, nullable=True)    # LSTM output 0.0–1.0


class Alert(Base):
    """
    An alert event triggered when the ML engine detects a critical condition.
    """
    __tablename__ = "alerts"

    id           = Column(Integer, primary_key=True, index=True)
    server_id    = Column(String(50), nullable=False, index=True)
    timestamp    = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    severity     = Column(String(20), nullable=False)    # WARNING / CRITICAL
    message      = Column(Text, nullable=False)          # Human-readable explanation
    metric       = Column(String(50), nullable=True)     # Which metric triggered it
    value        = Column(Float, nullable=True)          # The metric value at trigger
    failure_prob = Column(Float, nullable=True)          # ML failure probability
    acknowledged = Column(Boolean, nullable=False, default=False)
