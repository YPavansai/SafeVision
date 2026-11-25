#!/bin/sh
set -e

# Ensure media directory exists and copy bundled sample images/videos if empty
MEDIA_DIR="${MEDIA_ROOT:-/app/media}"
mkdir -p "$MEDIA_DIR"
if [ -d "/app/media/images" ] && [ ! -d "$MEDIA_DIR/images" ]; then
  cp -r /app/media/images "$MEDIA_DIR/images"
fi
if [ -d "/app/media/videos" ] && [ ! -d "$MEDIA_DIR/videos" ]; then
  cp -r /app/media/videos "$MEDIA_DIR/videos"
fi
mkdir -p "$MEDIA_DIR/outputs" "$MEDIA_DIR/reports" "$MEDIA_DIR/media_files" "$MEDIA_DIR/worker_photos" "$MEDIA_DIR/faces" "$MEDIA_DIR/violations"

echo "[SafeVision] Running database migrations..."
python manage.py migrate --noinput

echo "[SafeVision] Checking initial seed data..."
if ! python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safevision.settings'); django.setup(); from django.contrib.auth.models import User; raise SystemExit(0 if User.objects.exists() else 1)"; then
  echo "[SafeVision] Seeding initial database records..."
  python seed.py
fi

echo "[SafeVision] Starting Gunicorn server..."
exec gunicorn safevision.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 1 \
  --threads 4 \
  --timeout 120
