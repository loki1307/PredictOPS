# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend + ml models + simulator
COPY backend/ ./backend/
COPY ml/ ./ml/
COPY simulator/ ./simulator/

# Copy pre-built frontend static files (built locally before deploy)
COPY frontend/dist/ ./frontend/dist/

# Expose port
EXPOSE 8080

# Create data directory for SQLite persistence
RUN mkdir -p /data

# Point SQLite at the persistent volume
ENV DATABASE_URL="sqlite:////data/predictops.db"

# Run from backend/ directory so bare imports (database, models) resolve
CMD ["sh", "-c", "cd backend && uvicorn main:app --host 0.0.0.0 --port 8080"]
