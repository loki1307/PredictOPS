import time
import socket
import psutil
import requests
import subprocess
import re
import logging
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_URL = "http://localhost:8000"
POLL_INTERVAL = 3  # seconds
SERVER_ID = socket.gethostname()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("real_agent")

def get_ping_stats(host="8.8.8.8"):
    try:
        # Ping 1 packet
        output = subprocess.check_output(
            ["ping", "-n", "1", "-w", "1000", host], 
            universal_newlines=True, 
            stderr=subprocess.STDOUT
        )
        # Parse time
        time_match = re.search(r"time[=<](\d+)ms", output)
        latency = float(time_match.group(1)) if time_match else 0.0
        # Parse loss
        loss_match = re.search(r"\((\d+)% loss\)", output)
        loss = float(loss_match.group(1)) if loss_match else 0.0
        return latency, loss
    except subprocess.CalledProcessError:
        return 1000.0, 100.0  # 100% loss on timeout
    except Exception as e:
        log.error(f"Ping error: {e}")
        return 0.0, 0.0

def get_real_metrics():
    latency, loss = get_ping_stats()
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_io_percent": psutil.disk_usage('/').percent,
        "net_latency_ms": latency,
        "packet_loss_pct": loss,
    }

def run():
    ingest_url = f"{API_URL}/metrics/ingest"
    log.info(f"Real-Time Agent started — Server: {SERVER_ID} -> {ingest_url}")
    
    # Initialize cpu_percent block
    psutil.cpu_percent(interval=None)
    time.sleep(1)

    while True:
        metrics = get_real_metrics()
        
        batch = [{
            "server_id": SERVER_ID,
            "status": "healthy", # The backend updates this automatically
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **metrics
        }]

        try:
            resp = requests.post(ingest_url, json=batch, timeout=5)
            if resp.status_code == 200:
                log.info(f"Posted Real Metrics: CPU {metrics['cpu_percent']}% | RAM {metrics['memory_percent']}% | Ping {metrics['net_latency_ms']}ms")
            else:
                log.error(f"API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            log.warning(f"Cannot reach API: {exc}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run()
