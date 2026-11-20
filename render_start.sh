#!/usr/bin/env bash
python3 worker.py &
gunicorn web_app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8
