#!/bin/bash
service nginx start

source /app/.venv/bin/activate
cd /app/src
echo "Starting Ecuelle server on http://localhost:${APP_PORT}"
exec gunicorn --worker-class gevent -w 1 proxy:app --bind 0.0.0.0:5000