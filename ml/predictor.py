"""
predictor.py — ML inference engine for PredictOps.

Loads pre-trained models from ml/models/ and exposes a single
MLPredictor class that:
  1. Maintains a per-server rolling window of the last WINDOW_SIZE samples.
  2. Runs Isolation Forest on the latest sample to produce an anomaly score.
  3. Runs the LSTM on the rolling window to produce a failure probability.
"""

import os
import sys
import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Tuple

import numpy as np
import joblib

# Import MinimalLSTM so joblib can unpickle the saved LSTM model correctly
try:
    from lstm_model import MinimalLSTM  # noqa: F401 — needed for joblib unpickle
except ImportError:
    pass  # will still work for IF-only mode

log = logging.getLogger("predictor")

# ---------------------------------------------------------------------------
# Paths (relative to this file → works from both ml/ and backend/)
# ---------------------------------------------------------------------------
_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(_THIS_DIR, "models")

IF_MODEL_PATH  = os.path.join(_MODELS_DIR, "isolation_forest.pkl")
LSTM_MODEL_PATH = os.path.join(_MODELS_DIR, "lstm_model.pkl")   # NumPy LSTM (no TF)
SCALER_PATH    = os.path.join(_MODELS_DIR, "scaler.pkl")

# Number of time-steps the LSTM was trained on
WINDOW_SIZE = 30

# Feature order must match training
FEATURES = [
    "cpu_percent",
    "memory_percent",
    "disk_io_percent",
    "net_latency_ms",
    "packet_loss_pct",
]

# Risk level thresholds on failure_prob
RISK_THRESHOLDS = {
    "CRITICAL": 0.70,
    "HIGH":     0.45,
    "MEDIUM":   0.20,
    "LOW":      0.0,
}


def _risk_level(prob: float) -> str:
    for level, threshold in RISK_THRESHOLDS.items():
        if prob >= threshold:
            return level
    return "LOW"


# ---------------------------------------------------------------------------
# Singleton predictor
# ---------------------------------------------------------------------------
class MLPredictor:
    """
    Thread-safe ML predictor.

    Usage:
        predictor = MLPredictor()           # loads models once
        result = predictor.predict("web-01", metric_dict)
    """

    def __init__(self):
        self._lock   = threading.Lock()
        self._windows: Dict[str, deque] = {}   # server_id → deque of feature vectors
        self._if_model  = None
        self._lstm_model = None
        self._scaler    = None
        self._ready     = False
        self._load_models()

    # ------------------------------------------------------------------ #
    def _load_models(self):
        try:
            self._if_model   = joblib.load(IF_MODEL_PATH)
            self._scaler     = joblib.load(SCALER_PATH)
            self._lstm_model = joblib.load(LSTM_MODEL_PATH)  # MinimalLSTM or PyTorch wrapper

            self._ready = True
            log.info("ML models loaded successfully from %s", _MODELS_DIR)
        except FileNotFoundError as exc:
            log.warning(
                "Model files not found (%s). Run 'python ml/train.py' first. "
                "Predictor will return placeholder scores until models are available.",
                exc,
            )
        except Exception as exc:
            log.error("Failed to load models: %s", exc)

    # ------------------------------------------------------------------ #
    def _get_window(self, server_id: str) -> deque:
        if server_id not in self._windows:
            self._windows[server_id] = deque(maxlen=WINDOW_SIZE)
        return self._windows[server_id]

    # ------------------------------------------------------------------ #
    def predict(self, server_id: str, metrics: dict) -> Tuple[float, float, str]:
        """
        Returns (anomaly_score, failure_prob, risk_level).

        anomaly_score : float  Isolation Forest score. Negative = anomalous.
        failure_prob  : float  LSTM output, 0.0–1.0.
        risk_level    : str    LOW / MEDIUM / HIGH / CRITICAL
        """
        with self._lock:
            # Extract feature vector in the correct order
            vec = np.array([[metrics.get(f, 0.0) for f in FEATURES]], dtype=np.float32)

            # ── Fallback: no models loaded ────────────────────────────────
            if not self._ready:
                return self._heuristic_predict(metrics)

            # ── Scale features ────────────────────────────────────────────
            vec_scaled = self._scaler.transform(vec)

            # ── Isolation Forest ──────────────────────────────────────────
            anomaly_score = float(self._if_model.score_samples(vec_scaled)[0])

            # ── Update rolling window ─────────────────────────────────────
            window = self._get_window(server_id)
            window.append(vec_scaled[0])

            # ── LSTM ──────────────────────────────────────────────────────
            if len(window) < WINDOW_SIZE:
                # Pad with zeros at the front until we have a full window
                pad_count = WINDOW_SIZE - len(window)
                padded = np.zeros((WINDOW_SIZE, len(FEATURES)), dtype=np.float32)
                for i, row in enumerate(window):
                    padded[pad_count + i] = row
                lstm_input = padded
            else:
                lstm_input = np.array(list(window), dtype=np.float32)

            lstm_input  = lstm_input.reshape(1, WINDOW_SIZE, len(FEATURES))
            failure_prob = float(self._lstm_model.predict(lstm_input)[0])
            failure_prob = max(0.0, min(1.0, failure_prob))

            risk = _risk_level(failure_prob)
            return anomaly_score, failure_prob, risk

    # ------------------------------------------------------------------ #
    def _heuristic_predict(self, metrics: dict) -> Tuple[float, float, str]:
        """
        Rule-based fallback used when models are not yet trained.
        Provides reasonable scores so the dashboard is not completely empty.
        """
        cpu  = metrics.get("cpu_percent", 0)
        mem  = metrics.get("memory_percent", 0)
        lat  = metrics.get("net_latency_ms", 0)
        loss = metrics.get("packet_loss_pct", 0)

        # Simple weighted severity score 0–1
        score = (
            cpu  / 100 * 0.35 +
            mem  / 100 * 0.25 +
            min(lat, 500) / 500 * 0.25 +
            min(loss, 50) / 50  * 0.15
        )

        # Map to Isolation Forest-like score: high score → more negative (anomalous)
        anomaly_score = -score * 0.5

        failure_prob  = score ** 1.5   # exponential: only high values trigger alerts
        risk          = _risk_level(failure_prob)
        return anomaly_score, failure_prob, risk


# ---------------------------------------------------------------------------
# Module-level singleton — import this from other modules
# ---------------------------------------------------------------------------
predictor = MLPredictor()
