"""
patterns.py — Metric generation patterns for PredictOps simulator.

Provides three pattern types for each server metric:
  - NORMAL   : Healthy baseline with realistic jitter
  - DEGRADING: Slowly worsening trend leading toward failure
  - SPIKE    : Sudden short burst then return to normal
"""

import random
import math
import time


# ---------------------------------------------------------------------------
# Helper: bounded Gaussian noise
# ---------------------------------------------------------------------------
def _jitter(value: float, std: float = 2.0, lo: float = 0.0, hi: float = 100.0) -> float:
    """Add Gaussian noise to a value, clamped to [lo, hi]."""
    return max(lo, min(hi, value + random.gauss(0, std)))


# ---------------------------------------------------------------------------
# Server baseline profiles
# Each server type has different "normal" operating ranges
# ---------------------------------------------------------------------------
SERVER_PROFILES = {
    "web-01":   {"cpu": (15, 35), "mem": (40, 60), "disk_io": (10, 30), "net_latency": (5, 20),  "packet_loss": (0.0, 0.5)},
    "db-01":    {"cpu": (20, 50), "mem": (55, 75), "disk_io": (30, 60), "net_latency": (2, 10),  "packet_loss": (0.0, 0.3)},
    "cache-01": {"cpu": (5,  20), "mem": (70, 85), "disk_io": (5,  15), "net_latency": (1, 5),   "packet_loss": (0.0, 0.2)},
    "app-01":   {"cpu": (25, 55), "mem": (45, 65), "disk_io": (15, 35), "net_latency": (8, 25),  "packet_loss": (0.0, 0.6)},
    "queue-01": {"cpu": (10, 30), "mem": (30, 55), "disk_io": (20, 45), "net_latency": (3, 12),  "packet_loss": (0.0, 0.4)},
    "lb-01":    {"cpu": (8,  25), "mem": (25, 45), "disk_io": (5,  20), "net_latency": (1, 8),   "packet_loss": (0.0, 0.2)},
}


# ---------------------------------------------------------------------------
# Pattern classes
# ---------------------------------------------------------------------------

class NormalPattern:
    """
    Generates healthy baseline metrics with sinusoidal diurnal variation
    (simulating workload peaks) and realistic Gaussian jitter.
    """

    def __init__(self, profile: dict):
        self.profile = profile
        self.t = random.uniform(0, 2 * math.pi)   # random phase offset

    def next_sample(self) -> dict:
        self.t += 0.05                              # advance time step
        phase = math.sin(self.t) * 0.1             # ±10% amplitude diurnal swing

        def _metric(key, lo_extra=0, std=2.0):
            lo, hi = self.profile[key]
            mid = (lo + hi) / 2
            spread = (hi - lo) / 2
            base = mid + spread * phase
            return round(_jitter(base + lo_extra, std=std, lo=0.0, hi=100.0), 2)

        return {
            "cpu_percent":      _metric("cpu", std=3.0),
            "memory_percent":   _metric("mem", std=2.0),
            "disk_io_percent":  _metric("disk_io", std=4.0),
            "net_latency_ms":   round(_jitter((self.profile["net_latency"][0] + self.profile["net_latency"][1]) / 2, std=2.0, lo=0.0, hi=500.0), 2),
            "packet_loss_pct":  round(max(0.0, random.gauss(self.profile["packet_loss"][0], 0.15)), 3),
        }


class DegradingPattern:
    """
    Simulates a server slowly degrading toward failure over `duration_steps`
    data points. Metrics ramp up from normal baseline to critical levels.

    After the degrading window the pattern reports is_failed=True so the
    agent can reset the server to normal.
    """

    def __init__(self, profile: dict, duration_steps: int = 60):
        self.profile = profile
        self.duration = duration_steps
        self.step = 0
        self.normal = NormalPattern(profile)

    @property
    def is_failed(self) -> bool:
        return self.step >= self.duration

    @property
    def progress(self) -> float:
        """0.0 = just started degrading, 1.0 = full failure."""
        return min(1.0, self.step / self.duration)

    def next_sample(self) -> dict:
        base = self.normal.next_sample()
        p = self.progress

        # Exponential ramp so degradation accelerates near the end
        ramp = p ** 1.5

        # CPU spikes most dramatically
        base["cpu_percent"]     = round(min(99.9, base["cpu_percent"]     + ramp * 55), 2)
        base["memory_percent"]  = round(min(99.9, base["memory_percent"]  + ramp * 35), 2)
        base["disk_io_percent"] = round(min(99.9, base["disk_io_percent"] + ramp * 40), 2)
        base["net_latency_ms"]  = round(min(499.0, base["net_latency_ms"] + ramp * 200), 2)
        base["packet_loss_pct"] = round(min(50.0, base["packet_loss_pct"] + ramp * 20), 3)

        self.step += 1
        return base


class SpikePattern:
    """
    Generates a short, sharp spike in metrics then returns to normal.
    Useful for training the Isolation Forest to recognise sudden anomalies.
    """

    def __init__(self, profile: dict, spike_steps: int = 10):
        self.profile = profile
        self.spike_steps = spike_steps
        self.step = 0
        self.normal = NormalPattern(profile)

    @property
    def is_done(self) -> bool:
        return self.step >= self.spike_steps

    def next_sample(self) -> dict:
        base = self.normal.next_sample()
        if self.step < self.spike_steps:
            intensity = math.sin(math.pi * self.step / self.spike_steps)  # bell curve spike
            base["cpu_percent"]     = round(min(99.9, base["cpu_percent"]     + intensity * 60), 2)
            base["memory_percent"]  = round(min(99.9, base["memory_percent"]  + intensity * 30), 2)
            base["net_latency_ms"]  = round(min(499.0, base["net_latency_ms"] + intensity * 150), 2)
        self.step += 1
        return base
