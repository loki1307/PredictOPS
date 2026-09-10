"""
test_api.py — Comprehensive PredictOps API test script.
Run from project root: python test_api.py
"""
import requests, json, sys

BASE = "http://localhost:8000"
PASS_LIST = []
FAIL_LIST = []


def test(name, fn):
    try:
        result = fn()
        PASS_LIST.append(name)
        return result
    except Exception as e:
        FAIL_LIST.append((name, str(e)))
        return None


print("=" * 55)
print("  PredictOps API Test Suite")
print("=" * 55)

# -- 1. Health check ----------------------------------------
r = requests.get(f"{BASE}/health", timeout=5)
if r.status_code == 200 and r.json().get("status") == "ok":
    PASS_LIST.append("GET /health -> 200 ok")
    print(f"  Health: {r.json()}")
else:
    FAIL_LIST.append(("GET /health", f"status={r.status_code}"))

# -- 2. Servers summary ------------------------------------
r = requests.get(f"{BASE}/servers/summary", timeout=5)
if r.status_code == 200:
    data = r.json()
    PASS_LIST.append(f"GET /servers/summary -> {len(data)} servers")
    print(f"\n  Servers ({len(data)} total):")
    for s in data:
        prob_pct = round(s["failure_prob"] * 100, 1)
        print(f"    {s['server_id']:12s}  status={s['status']:8s}  risk={s['risk_level']:8s}  prob={prob_pct}%  cpu={s['cpu_percent']}%")
else:
    FAIL_LIST.append(("GET /servers/summary", f"HTTP {r.status_code}: {r.text[:100]}"))

# -- 3. Metrics per server ---------------------------------
print("\n  Metrics history:")
for sid in ["web-01", "db-01", "cache-01"]:
    r = requests.get(f"{BASE}/metrics/{sid}", params={"limit": 5}, timeout=5)
    if r.status_code == 200:
        rows = r.json()
        if rows:
            last = rows[-1]
            PASS_LIST.append(f"GET /metrics/{sid} -> {len(rows)} rows")
            print(f"    {sid}: {len(rows)} rows, latest cpu={last['cpu_percent']}%  mem={last['memory_percent']}%  anomaly={last.get('anomaly_score', 'N/A')}")
        else:
            PASS_LIST.append(f"GET /metrics/{sid} -> empty (no data yet)")
            print(f"    {sid}: no data yet")
    else:
        FAIL_LIST.append((f"GET /metrics/{sid}", f"HTTP {r.status_code}"))

# -- 4. Predictions ----------------------------------------
print("\n  ML Predictions:")
for sid in ["web-01", "db-01"]:
    r = requests.get(f"{BASE}/predictions/{sid}", timeout=5)
    if r.status_code == 200:
        d = r.json()
        PASS_LIST.append(f"GET /predictions/{sid}")
        prob_pct = round(d["failure_prob"] * 100, 1)
        print(f"    {sid}: prob={prob_pct}%  anomaly={round(d['anomaly_score'],4)}  risk={d['risk_level']}")
    elif r.status_code == 404:
        PASS_LIST.append(f"GET /predictions/{sid} -> 404 (no data yet)")
        print(f"    {sid}: 404 (no ingested data yet)")
    else:
        FAIL_LIST.append((f"GET /predictions/{sid}", f"HTTP {r.status_code}"))

# -- 5. Alerts list ----------------------------------------
r = requests.get(f"{BASE}/alerts", params={"limit": 10}, timeout=5)
if r.status_code == 200:
    alerts = r.json()
    PASS_LIST.append(f"GET /alerts -> {len(alerts)} alerts")
    print(f"\n  Alerts ({len(alerts)} recent):")
    for a in alerts[:5]:
        print(f"    [{a['severity']:8s}] {a['server_id']:10s}  prob={round((a['failure_prob'] or 0)*100)}%  acked={a['acknowledged']}")
        print(f"             {a['message'][:80]}")
else:
    FAIL_LIST.append(("GET /alerts", f"HTTP {r.status_code}: {r.text[:100]}"))

# -- 6. Alert stats ----------------------------------------
r = requests.get(f"{BASE}/alerts/stats/summary", timeout=5)
if r.status_code == 200:
    PASS_LIST.append("GET /alerts/stats/summary")
    print(f"\n  Alert counts: {r.json()}")
else:
    FAIL_LIST.append(("GET /alerts/stats/summary", f"HTTP {r.status_code}"))

# -- 7. Ingest — critical payload --------------------------
payload = [
    {
        "server_id": "web-01",
        "cpu_percent": 96.5,
        "memory_percent": 93.2,
        "disk_io_percent": 89.0,
        "net_latency_ms": 380.0,
        "packet_loss_pct": 22.0,
        "status": "critical",
    }
]
r = requests.post(f"{BASE}/metrics/ingest", json=payload, timeout=5)
if r.status_code == 200:
    d = r.json()
    PASS_LIST.append("POST /metrics/ingest (critical)")
    pred = d["predictions"][0]
    print(f"\n  Manual ingest (critical): stored={d['stored']}  prob={round(pred['failure_prob']*100,1)}%  risk={pred['risk_level']}")
else:
    FAIL_LIST.append(("POST /metrics/ingest", f"HTTP {r.status_code}: {r.text[:200]}"))

# -- 8. Ingest — normal payload ----------------------------
payload_normal = [
    {
        "server_id": "cache-01",
        "cpu_percent": 12.0,
        "memory_percent": 72.0,
        "disk_io_percent": 8.0,
        "net_latency_ms": 3.0,
        "packet_loss_pct": 0.0,
    }
]
r = requests.post(f"{BASE}/metrics/ingest", json=payload_normal, timeout=5)
if r.status_code == 200:
    d = r.json()
    PASS_LIST.append("POST /metrics/ingest (normal)")
    pred = d["predictions"][0]
    print(f"  Manual ingest (normal):   stored={d['stored']}  prob={round(pred['failure_prob']*100,1)}%  risk={pred['risk_level']}")
else:
    FAIL_LIST.append(("POST /metrics/ingest (normal)", f"HTTP {r.status_code}: {r.text[:200]}"))

# -- 9. Ingest — malformed payload (validation test) -------
r = requests.post(f"{BASE}/metrics/ingest", json=[{"server_id": "bad"}], timeout=5)
if r.status_code == 422:
    PASS_LIST.append("POST /metrics/ingest malformed -> 422 validation error [PASS]")
    print(f"\n  Malformed payload -> HTTP 422 (correct validation error)")
else:
    FAIL_LIST.append(("POST /metrics/ingest malformed", f"Expected 422 got {r.status_code}"))

# -- 10. 404 for unknown server prediction -----------------
r = requests.get(f"{BASE}/predictions/nonexistent-99", timeout=5)
if r.status_code == 404:
    PASS_LIST.append("GET /predictions/nonexistent-99 -> 404 [PASS]")
else:
    FAIL_LIST.append(("GET /predictions/nonexistent", f"Expected 404 got {r.status_code}"))

# -- 11. Alert acknowledge ---------------------------------
r_alerts = requests.get(f"{BASE}/alerts?limit=1", timeout=5)
if r_alerts.status_code == 200 and r_alerts.json():
    alert_id = r_alerts.json()[0]["id"]
    r = requests.post(f"{BASE}/alerts/{alert_id}/acknowledge", json={"acknowledged": True}, timeout=5)
    if r.status_code == 200 and r.json()["acknowledged"]:
        PASS_LIST.append(f"POST /alerts/{alert_id}/acknowledge -> acknowledged=true [PASS]")
        print(f"\n  Alert #{alert_id} acknowledged OK")
    else:
        FAIL_LIST.append((f"POST /alerts/{alert_id}/acknowledge", f"HTTP {r.status_code}"))

# -- 12. Filtered alerts -----------------------------------
r = requests.get(f"{BASE}/alerts", params={"severity": "CRITICAL", "limit": 5}, timeout=5)
if r.status_code == 200:
    critical_alerts = r.json()
    PASS_LIST.append(f"GET /alerts?severity=CRITICAL -> {len(critical_alerts)} critical alerts")
    print(f"  Critical-only alerts: {len(critical_alerts)} found")
else:
    FAIL_LIST.append(("GET /alerts?severity=CRITICAL", f"HTTP {r.status_code}"))

# -- Results -----------------------------------------------
print()
print("=" * 55)
print(f"  RESULTS: {len(PASS_LIST)} passed, {len(FAIL_LIST)} failed")
print("=" * 55)
for p in PASS_LIST:
    print(f"  PASS: {p}")
if FAIL_LIST:
    print("\nFAILED:")
    for name, err in FAIL_LIST:
        print(f"  FAIL: {name}")
        print(f"    {err}")
    sys.exit(1)
else:
    print("\n  All tests passed! SUCCESS")
