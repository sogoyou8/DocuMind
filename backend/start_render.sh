#!/bin/sh
set -eu
python manage.py migrate --noinput
if [ "${DOCUMIND_DEMO_READONLY:-0}" = "1" ]; then
  python manage.py seed_demo
fi
exec gunicorn documind_api.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 1 --threads 2 --timeout 90 --access-logfile -
