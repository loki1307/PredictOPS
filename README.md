# PredictOps ⚡

**AIOps-based Predictive Server & Network Failure Detection System**

> *Traditional monitoring alerts after failures happen. PredictOps predicts them before they do.*

Built as a Final Year IT Engineering academic project demo.

---

## 🏗️ Architecture

```
┌─────────────────┐    POST /metrics/ingest     ┌──────────────────────┐
│  Simulator      │ ────────────────────────────▶│  FastAPI Backend     │
│  (6 VMs)        │                              │  SQLite Database     │
└─────────────────┘                              │  ML Predictor        │
                                                 └──────────┬───────────┘
                                                            │ REST API
                                                 ┌──────────▼───────────┐
                                                 │  React Dashboard     │
                                                 │  Recharts + Tailwind │
                                                 └──────────────────────┘
```

## 🧠 ML Models

| Model | Purpose | Algorithm |
|---|---|---|
| Isolation Forest | Real-time anomaly detection | sklearn |
| LSTM | Failure probability (next 15 min) | TensorFlow/Keras |
| Robust Scaler | Feature normalisation | sklearn |

---

## 📁 Folder Structure

```
PredictOPS/
├── backend/          ← FastAPI REST API + SQLite
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── metrics.py      ← ingest + alert engine
│   │   ├── predictions.py
│   │   └── alerts.py
│   └── requirements.txt
│
├── ml/               ← ML training + inference
│   ├── train.py      ← run this once to generate models
│   ├── predictor.py  ← inference class (imported by backend)
│   ├── models/       ← saved .pkl and .keras files (auto-created)
│   └── requirements.txt
│
├── simulator/        ← Synthetic data generator
│   ├── agent.py      ← run this to stream metrics to the backend
│   └── patterns.py   ← Normal / Degrading / Spike patterns
│
├── frontend/         ← React + Tailwind + Recharts dashboard
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── pages/
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- pip + npm

---

### Step 1 — Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Note:** TensorFlow (~600 MB) is included. If you have a slow connection, this step may take a few minutes.

---

### Step 2 — Train the ML Models

```bash
# From the project root
python ml/train.py
```

This generates `ml/models/isolation_forest.pkl`, `lstm_model.keras`, and `scaler.pkl`.  
Expected runtime: **1–3 minutes** on CPU.

```
Sample output:
  Dataset: 10,450 samples, 8.7% anomalies
  IF: flagged 1,045/10,450 samples as anomalies
  LSTM — val_loss=0.0821  val_acc=0.9412  val_auc=0.9734
  Training complete in 87.3 seconds ✓
```

---

### Step 3 — Start the Backend API

```bash
# From the project root
uvicorn backend.main:app --reload --port 8000
```

Verify: open [http://localhost:8000/docs](http://localhost:8000/docs) — the Swagger UI should appear.

---

### Step 4 — Install & Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) 🎉

---

### Step 5 — Start the Simulator

```bash
# From the project root (in a new terminal)
python simulator/agent.py --interval 3
```

This streams live metrics from 6 simulated servers every 3 seconds.  
Watch the dashboard update in real time!

---

## 🖥️ Simulated Servers

| Server | Role | Normal CPU | Normal Mem |
|---|---|---|---|
| web-01 | Web server | 15–35% | 40–60% |
| db-01 | Database | 20–50% | 55–75% |
| cache-01 | Cache layer | 5–20% | 70–85% |
| app-01 | Application | 25–55% | 45–65% |
| queue-01 | Message queue | 10–30% | 30–55% |
| lb-01 | Load balancer | 8–25% | 25–45% |

---

## 📊 Dashboard Features

| Feature | Description |
|---|---|
| **Server Grid** | 6 server cards with live CPU/Mem/Latency mini-bars |
| **Status Badges** | 🟢 Healthy / 🟡 Warning / 🔴 Critical |
| **Failure Gauge** | Radial chart showing LSTM failure probability % |
| **Live Charts** | Multi-line time-series for all 5 metrics |
| **Alert Table** | Timestamped alerts with one-click acknowledgement |
| **Filter Tabs** | Filter servers by status |
| **Auto-refresh** | Every 5 seconds, no page reload needed |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/metrics/ingest` | Ingest batch of metrics from simulator |
| `GET` | `/metrics/{server_id}` | Fetch metric history |
| `GET` | `/servers/summary` | Get all server current states |
| `GET` | `/predictions/{server_id}` | Get latest ML prediction |
| `GET` | `/alerts` | List alerts (filterable) |
| `POST` | `/alerts/{id}/acknowledge` | Acknowledge an alert |
| `GET` | `/health` | API liveness probe |

Full interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ⚙️ Configuration

### Simulator
Edit `simulator/agent.py`:
```python
POLL_INTERVAL = 3       # seconds between posts
DEGRADE_PROB  = 0.003   # probability of starting a degrading pattern each tick
SPIKE_PROB    = 0.005   # probability of starting a spike each tick
```

### Alert Thresholds
Edit `backend/routers/metrics.py`:
```python
ALERT_COOLDOWN_MINUTES = 5      # min time between alerts per server

# In the ingest loop:
if failure_prob >= 0.70:  → CRITICAL alert
if anomaly_score < -0.10 and failure_prob >= 0.30:  → WARNING alert
```

---

## 🧪 How It Works

### 1. Data Generation
The simulator's `DegradingPattern` ramps CPU, Memory, Disk I/O and Network Latency
exponentially over 40–80 time steps. This mimics real-world gradual degradation
(e.g., memory leak, runaway process, network congestion).

### 2. Isolation Forest
Trained on the full dataset (normal + anomalous rows). Assigns a continuous
anomaly score to each incoming data point. Highly negative scores indicate
the point falls far from the normal cluster.

### 3. LSTM Failure Prediction
Trained on sliding windows of 30 consecutive samples, labelled `1` if a
failure occurs within the next 15 samples. Learns temporal degradation patterns
and outputs a 0–1 probability.

### 4. Alert Engine
Integrated into the ingest endpoint:
- CRITICAL if `failure_prob ≥ 0.70`
- WARNING if `anomaly_score < -0.10 AND failure_prob ≥ 0.30`
- 5-minute cooldown per server to prevent alert storms

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10, FastAPI, SQLAlchemy 2, SQLite |
| **ML** | scikit-learn (Isolation Forest), TensorFlow/Keras (LSTM) |
| **Frontend** | React 18, Vite, Tailwind CSS 3, Recharts |
| **Simulator** | Pure Python with NumPy-free pattern generators |

---

## 🎓 Academic Notes

This project demonstrates:
- **Time-series anomaly detection** using unsupervised learning (Isolation Forest)
- **Sequence-to-label prediction** using LSTM networks
- **Microservices architecture** with REST APIs
- **Real-time data streaming** from agent to dashboard
- **Full-stack integration** of ML models into a production-style web app

---

*Built with ❤️ for Final Year IT Engineering — AIOps Project Demo*
