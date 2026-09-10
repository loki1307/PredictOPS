"""
train.py — PredictOps ML Training Script

Generates a large synthetic dataset using the simulator patterns, then trains:
  1. Isolation Forest    — real-time anomaly detection (scikit-learn)
  2. MinimalLSTM         — time-series failure probability prediction
                          Pure NumPy implementation: no TensorFlow, PyTorch,
                          or any deep-learning library required.
                          Works perfectly on any Python 3.10+ install.

Saves trained models + scaler to ml/models/.

Usage (from project root):
    python ml/train.py

Expected runtime: ~30-90 seconds on CPU.
"""

import os
import sys
import logging
import random
import numpy as np
import joblib
from datetime import datetime

# ── Ensure simulator/ is on the path for importing patterns ─────────────────
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR    = os.path.dirname(_THIS_DIR)
_MODELS_DIR  = os.path.join(_THIS_DIR, "models")
_SIM_DIR     = os.path.join(_ROOT_DIR, "simulator")

sys.path.insert(0, _SIM_DIR)

from patterns import SERVER_PROFILES, NormalPattern, DegradingPattern, SpikePattern
from lstm_model import MinimalLSTM   # shared model definition (importable by predictor.py)  # type: ignore[import-not-found]

os.makedirs(_MODELS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("train")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
FEATURES = [
    "cpu_percent",
    "memory_percent",
    "disk_io_percent",
    "net_latency_ms",
    "packet_loss_pct",
]

WINDOW_SIZE       = 30     # LSTM sequence length
NORMAL_SAMPLES    = 8000   # normal rows per server (across all servers)
DEGRADE_EPISODES  = 40     # number of degrading episodes to simulate
SPIKE_EPISODES    = 30     # number of spike episodes to simulate
LSTM_EPOCHS       = 60
BATCH_SIZE        = 64
LEARNING_RATE     = 0.01
RANDOM_SEED       = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ---------------------------------------------------------------------------
# Step 1: Generate synthetic dataset
# ---------------------------------------------------------------------------
def generate_dataset():
    """
    Returns (X, y_binary) where:
      X        : (N, n_features) float32 — raw metric rows
      y_binary : (N,) int8        — 1 = failure/anomaly, 0 = normal
    """
    log.info("Generating synthetic dataset…")
    X_rows  = []
    y_rows  = []
    servers = list(SERVER_PROFILES.keys())

    # ── Normal samples ────────────────────────────────────────────────────
    samples_per_server = NORMAL_SAMPLES // len(servers)
    for sid in servers:
        pat = NormalPattern(SERVER_PROFILES[sid])
        for _ in range(samples_per_server):
            s = pat.next_sample()
            X_rows.append([s[f] for f in FEATURES])
            y_rows.append(0)

    # ── Degrading episodes ────────────────────────────────────────────────
    for _ in range(DEGRADE_EPISODES):
        sid  = random.choice(servers)
        pat  = DegradingPattern(SERVER_PROFILES[sid], duration_steps=random.randint(40, 80))
        while not pat.is_failed:
            s = pat.next_sample()
            X_rows.append([s[f] for f in FEATURES])
            y_rows.append(1 if pat.progress > 0.5 else 0)
        for _ in range(10):
            X_rows.append([99.0, 95.0, 95.0, 450.0, 30.0])
            y_rows.append(1)

    # ── Spike episodes ────────────────────────────────────────────────────
    for _ in range(SPIKE_EPISODES):
        sid  = random.choice(servers)
        pat  = SpikePattern(SERVER_PROFILES[sid], spike_steps=random.randint(8, 14))
        while not pat.is_done:
            s = pat.next_sample()
            X_rows.append([s[f] for f in FEATURES])
            y_rows.append(1 if pat.step > pat.spike_steps * 0.3 else 0)

    X = np.array(X_rows, dtype=np.float32)
    y = np.array(y_rows, dtype=np.int8)
    log.info("Dataset: %d samples, %d anomalies (%.1f%%)",
             len(X), y.sum(), 100 * y.mean())
    return X, y


# ---------------------------------------------------------------------------
# Step 2: Scale features
# ---------------------------------------------------------------------------
def fit_scaler(X: np.ndarray):
    from sklearn.preprocessing import RobustScaler
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    scaler_path = os.path.join(_MODELS_DIR, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    log.info("Scaler saved → %s", scaler_path)
    return scaler, X_scaled


# ---------------------------------------------------------------------------
# Step 3: Train Isolation Forest
# ---------------------------------------------------------------------------
def train_isolation_forest(X_scaled: np.ndarray):
    from sklearn.ensemble import IsolationForest
    log.info("Training Isolation Forest…")
    clf = IsolationForest(
        n_estimators   = 200,
        contamination  = 0.10,
        max_features   = 1.0,
        random_state   = RANDOM_SEED,
        n_jobs         = -1,
    )
    clf.fit(X_scaled)
    anomaly_count = (clf.predict(X_scaled) == -1).sum()
    log.info("IF: flagged %d/%d samples as anomalies (%.1f%%)",
             anomaly_count, len(X_scaled), 100 * anomaly_count / len(X_scaled))
    model_path = os.path.join(_MODELS_DIR, "isolation_forest.pkl")
    joblib.dump(clf, model_path)
    log.info("Isolation Forest saved → %s", model_path)
    return clf


# ---------------------------------------------------------------------------
# Step 4: Build LSTM sequences
# ---------------------------------------------------------------------------
def build_lstm_sequences(X_scaled: np.ndarray, y: np.ndarray):
    log.info("Building LSTM sequences (window=%d)…", WINDOW_SIZE)
    FUTURE_STEPS = 15
    Xs, ys = [], []
    for i in range(len(X_scaled) - WINDOW_SIZE - FUTURE_STEPS):
        window       = X_scaled[i : i + WINDOW_SIZE]
        future_label = y[i + WINDOW_SIZE : i + WINDOW_SIZE + FUTURE_STEPS].max()
        Xs.append(window)
        ys.append(float(future_label))
    Xs = np.array(Xs, dtype=np.float32)
    ys = np.array(ys, dtype=np.float32)
    log.info("LSTM dataset: %d sequences, %.1f%% positive", len(Xs), 100 * ys.mean())
    return Xs, ys




def train_lstm(Xs: np.ndarray, ys: np.ndarray):
    log.info("Training MinimalLSTM (pure NumPy)…")
    n_features = Xs.shape[2]
    split       = int(len(Xs) * 0.85)
    X_train, X_val = Xs[:split], Xs[split:]
    y_train, y_val = ys[:split], ys[split:]

    model = MinimalLSTM(input_size=n_features, h1=32, h2=16)
    model.fit(X_train, y_train, X_val, y_val,
              epochs=LSTM_EPOCHS, batch_size=BATCH_SIZE, lr=LEARNING_RATE)

    model_path = os.path.join(_MODELS_DIR, "lstm_model.pkl")
    joblib.dump(model, model_path)
    log.info("LSTM model saved → %s", model_path)
    return model


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log.info("=== PredictOps ML Training ===")
    start = datetime.now()

    X, y       = generate_dataset()
    scaler, Xs = fit_scaler(X)
    train_isolation_forest(Xs)
    Xl, yl     = build_lstm_sequences(Xs, y)
    train_lstm(Xl, yl)

    elapsed = (datetime.now() - start).total_seconds()
    log.info("Training complete in %.1f seconds ✓", elapsed)
    log.info("Models saved to %s", _MODELS_DIR)
