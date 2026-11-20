#!/usr/bin/env bash
python3 -u worker.py &
exec gunicorn web_app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 120
