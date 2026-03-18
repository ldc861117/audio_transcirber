#!/bin/bash
set -e

echo "🚀 Starting Audio Transcriber..."

# Start Nginx in background
echo "  → Starting Nginx on port ${PORT:-8080}..."
nginx

# Start Gunicorn (Flask backend)
echo "  → Starting Gunicorn on port 5099..."
exec gunicorn \
  --bind 127.0.0.1:5099 \
  --workers 2 \
  --threads 4 \
  --timeout 600 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  "backend.app:create_app('production')"
