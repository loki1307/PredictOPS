"""
agent.py — PredictOps Metrics Simulator Agent

Simulates 6 virtual servers, each with an independent state machine:
    NORMAL → DEGRADING → FAILED → (auto-recover) → NORMAL

Posts a batch of metrics for all servers to the backend API every
POLL_INTERVAL seconds.

Usage:
    python simulator/agent.py [--api-url http://localhost:8000] [--interval 3]
"""

import argparse
import json
import logging
import random
import time
from datetime import datetime, timezone

import requests

from patterns import SERVER_PROFILES, NormalPattern, DegradingPattern, SpikePattern

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_API_URL = "http://localhost:8000"
POLL_INTERVAL   = 3          # seconds between metric posts
DEGRADE_PROB    = 0.003      # probability per tick of starting a degrading event
SPIKE_PROB      = 0.005      # probability per tick of starting a spike event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("simulator")


# ---------------------------------------------------------------------------
# Server state machine
# ---------------------------------------------------------------------------
class ServerAgent:
    """
    Manages the metric-generation state for one virtual server.

    State transitions:
        NORMAL     → DEGRADING  (random trigger, DEGRADE_PROB per tick)
        NORMAL     → SPIKE      (random trigger, SPIKE_PROB per tick)
        DEGRADING  → FAILED     (when DegradingPattern.is_failed)
        FAILED     → NORMAL     (after random recovery delay 5-15 ticks)
        SPIKE      → NORMAL     (when SpikePattern.is_done)
    """

    NORMAL    = "NORMAL"
    DEGRADING = "DEGRADING"
    FAILED    = "FAILED"
    SPIKE     = "SPIKE"

    def __init__(self, server_id: str):
        self.server_id = server_id
        self.profile   = SERVER_PROFILES[server_id]
        self.state     = self.NORMAL
        self._pattern  = NormalPattern(self.profile)
        self._recover_in = 0

    # ------------------------------------------------------------------ #
    def tick(self) -> dict:
        """Advance the state machine and return the next metric sample."""

        # ── FAILED: count down recovery ──────────────────────────────────
        if self.state == self.FAILED:
            self._recover_in -= 1
            if self._recover_in <= 0:
                log.info("[%s] Recovered → NORMAL", self.server_id)
                self._transition_to_normal()
            # During failure: return maxed-out metrics
            return self._failure_metrics()

        # ── DEGRADING: advance pattern, check completion ─────────────────
        if self.state == self.DEGRADING:
            sample = self._pattern.next_sample()
            if self._pattern.is_failed:
                log.warning("[%s] Failure event! → FAILED", self.server_id)
                self.state = self.FAILED
                self._recover_in = random.randint(5, 15)
            return sample

        # ── SPIKE: advance, check done ───────────────────────────────────
        if self.state == self.SPIKE:
            sample = self._pattern.next_sample()
            if self._pattern.is_done:
                log.info("[%s] Spike done → NORMAL", self.server_id)
                self._transition_to_normal()
            return sample

        # ── NORMAL: maybe trigger an event ───────────────────────────────
        if random.random() < DEGRADE_PROB:
            log.warning("[%s] Starting DEGRADING pattern", self.server_id)
            self.state    = self.DEGRADING
            self._pattern = DegradingPattern(self.profile, duration_steps=random.randint(40, 80))
        elif random.random() < SPIKE_PROB:
            log.info("[%s] Starting SPIKE pattern", self.server_id)
            self.state    = self.SPIKE
            self._pattern = SpikePattern(self.profile, spike_steps=random.randint(8, 14))

        return self._pattern.next_sample()

    # ------------------------------------------------------------------ #
    def _transition_to_normal(self):
        self.state    = self.NORMAL
        self._pattern = NormalPattern(self.profile)

    def _failure_metrics(self) -> dict:
        """Return critically high metrics during a failure state."""
        return {
            "cpu_percent":     round(random.uniform(95, 100), 2),
            "memory_percent":  round(random.uniform(90, 100), 2),
            "disk_io_percent": round(random.uniform(85, 100), 2),
            "net_latency_ms":  round(random.uniform(300, 500), 2),
            "packet_loss_pct": round(random.uniform(20, 50), 3),
        }

    @property
    def status(self) -> str:
        """Return human-readable server status."""
        return {
            self.NORMAL:    "healthy",
            self.DEGRADING: "warning",
            self.SPIKE:     "warning",
            self.FAILED:    "critical",
        }[self.state]


# ---------------------------------------------------------------------------
# Main simulator loop
# ---------------------------------------------------------------------------
def run(api_url: str, interval: float):
    ingest_url = f"{api_url}/metrics/ingest"

    # Instantiate all servers
    servers = {sid: ServerAgent(sid) for sid in SERVER_PROFILES}
    log.info("Simulator started — %d servers → %s", len(servers), ingest_url)

    while True:
        batch = []
        for sid, agent in servers.items():
            metrics = agent.tick()
            batch.append({
                "server_id":      sid,
                "status":         agent.status,
                "timestamp":      datetime.now(timezone.utc).isoformat(),
                **metrics,
            })

        # POST the entire batch in one request
        try:
            resp = requests.post(ingest_url, json=batch, timeout=5)
            if resp.status_code == 200:
                log.debug("Batch of %d metrics posted OK", len(batch))
            else:
                log.error("API returned %s: %s", resp.status_code, resp.text[:200])
        except requests.exceptions.ConnectionError:
            log.warning("Cannot reach API at %s — retrying in %ds", api_url, interval)
        except Exception as exc:
            log.error("Unexpected error: %s", exc)

        time.sleep(interval)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PredictOps Metrics Simulator")
    parser.add_argument("--api-url",  default=DEFAULT_API_URL, help="Backend API base URL")
    parser.add_argument("--interval", default=POLL_INTERVAL,   type=float, help="Seconds between posts")
    args = parser.parse_args()

    run(api_url=args.api_url, interval=args.interval)
