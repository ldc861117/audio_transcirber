# ============================================================
# Multi-stage Dockerfile for Audio Transcriber
# Stage 1: Build frontend (Node)
# Stage 2: Production server (Python + Nginx)
# ============================================================

# ── Stage 1: Frontend Build ─────────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Production Server ──────────────────────────────
FROM python:3.10-slim

# Install system deps: ffmpeg (audio processing) + nginx (reverse proxy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements-server.txt ./
RUN pip install --no-cache-dir -r requirements-server.txt

# Copy backend code and root-level modules
COPY backend/ ./backend/
COPY app_paths.py ./
COPY .env.example ./.env.example

# Copy frontend build output
COPY --from=frontend-build /app/frontend/dist /app/static/dist

# Copy nginx config and entrypoint
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Create data directory for SQLite
RUN mkdir -p /app/data

# Cloud Run provides PORT env var (default 8080)
ENV PORT=8080
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["./entrypoint.sh"]
