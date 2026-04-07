#!/bin/bash
source /app/.venv/bin/activate
cd /app/src
gunicorn --worker-class gevent -w 1 proxy:app --bind 0.0.0.0:5000