# start_all.ps1 — Launch all PredictOps services in separate terminal windows
# Run from the project root: .\start_all.ps1

$root = $PSScriptRoot

Write-Host ""
Write-Host "Starting PredictOps services..." -ForegroundColor Cyan
Write-Host ""

# ── Backend API ──────────────────────────────────────────────────────────────
Write-Host "  Launching Backend API at http://localhost:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; python -m uvicorn main:app --reload --port 8000"

Start-Sleep -Seconds 3

# ── React Frontend ───────────────────────────────────────────────────────────
Write-Host "  Launching Dashboard at http://localhost:5173" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Start-Sleep -Seconds 2

# ── Simulator ────────────────────────────────────────────────────────────────
Write-Host "  Launching Metrics Simulator" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; python simulator/agent.py --interval 3"

Write-Host ""
Write-Host "All services started!" -ForegroundColor Cyan
Write-Host "  Dashboard: http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
