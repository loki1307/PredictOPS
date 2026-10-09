"""
main.py — PredictOps FastAPI application entry point.

Mounts all routers, configures CORS (so the React dev server can call the API),
and creates the SQLite tables on startup.

Run with:
    uvicorn backend.main:app --reload --port 8000
  OR (from the backend/ directory):
    uvicorn main:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import engine, Base  # type: ignore[import-not-found]
# Import models so SQLAlchemy registers them before create_all()
import models  # noqa: F401  # type: ignore[import-not-found]
from routers.metrics     import router as metrics_router, servers_router  # type: ignore[import-not-found]
from routers.predictions import router as predictions_router  # type: ignore[import-not-found]
from routers.alerts      import router as alerts_router  # type: ignore[import-not-found]
from routers.auth        import router as auth_router, get_current_user
from fastapi import Depends

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Lifespan: create DB tables on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Creating database tables (if not exist)…")
    Base.metadata.create_all(bind=engine)
    log.info("PredictOps backend is ready ✓")
    yield
    log.info("Shutting down PredictOps backend.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title       = "PredictOps API",
    description = "AIOps Predictive Server & Network Failure Detection System",
    version     = "1.0.0",
    lifespan    = lifespan,
)

# Allow requests from the Vite dev server and any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ---------------------------------------------------------------------------
# Mount routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(metrics_router, dependencies=[Depends(get_current_user)])
app.include_router(servers_router, dependencies=[Depends(get_current_user)])
app.include_router(predictions_router, dependencies=[Depends(get_current_user)])
app.include_router(alerts_router, dependencies=[Depends(get_current_user)])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health():
    """Simple liveness probe."""
    return {"status": "ok", "service": "PredictOps API"}


# ---------------------------------------------------------------------------
# Serve React frontend static build (production only)
# ---------------------------------------------------------------------------
_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

    # Known API path prefixes — never serve index.html for these
    _API_PREFIXES = ("/auth", "/metrics", "/servers", "/predictions", "/alerts", "/health", "/docs", "/openapi.json")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        """Return index.html for all non-API routes (SPA client-side routing)."""
        if full_path and any(full_path.startswith(p.lstrip("/")) for p in _API_PREFIXES):
            raise HTTPException(status_code=404, detail="Not found")
        index = _DIST / "index.html"
        return FileResponse(str(index))
