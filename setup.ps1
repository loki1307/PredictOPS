# setup.ps1 — PredictOps one-click setup script for Windows
# Run from the project root: .\setup.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PredictOps Setup Script              " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Python packages ───────────────────────────────────────────────────────
Write-Host "[1/4] Installing Python packages..." -ForegroundColor Yellow
python -m pip install fastapi "uvicorn[standard]" sqlalchemy pydantic python-multipart requests joblib aiofiles -q
python -m pip install scikit-learn --only-binary :all: -q
python -m pip install tensorflow --only-binary :all: -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: TensorFlow install failed — backend will use heuristic fallback." -ForegroundColor Yellow
} else {
    Write-Host "  ✓ Python packages installed" -ForegroundColor Green
}

# ── 2. Train ML models ───────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Training ML models (takes 1-3 minutes)..." -ForegroundColor Yellow
python ml/train.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ ML models trained and saved to ml/models/" -ForegroundColor Green
} else {
    Write-Host "  WARN: Training failed — check output above." -ForegroundColor Yellow
}

# ── 3. Frontend packages ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Installing frontend packages..." -ForegroundColor Yellow
Set-Location frontend
npm install
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Frontend packages installed" -ForegroundColor Green
} else {
    Write-Host "  ERROR: npm install failed. Is Node.js installed?" -ForegroundColor Red
    Write-Host "  Install from: https://nodejs.org/en/download" -ForegroundColor Gray
}
Set-Location ..

# ── 4. Summary ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start PredictOps, run: .\start_all.ps1" -ForegroundColor White
Write-Host "Or start each service manually:" -ForegroundColor Gray
Write-Host "  Terminal 1: python -m uvicorn backend.main:app --reload --port 8000" -ForegroundColor Gray
Write-Host "  Terminal 2: cd frontend; npm run dev" -ForegroundColor Gray
Write-Host "  Terminal 3: python simulator/agent.py" -ForegroundColor Gray
Write-Host ""
