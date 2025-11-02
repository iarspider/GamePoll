#!/usr/bin/env sh
set -e

# Собираем статику в примонтированную папку
python manage.py collectstatic --noinput

# (опционально) миграции
python manage.py migrate --noinput

# Запускаем gunicorn/uvicorn
exec gunicorn GamePoll.wsgi:application \
  --bind "${GUNICORN_BIND:-0.0.0.0:8000}" \
  --workers "${GUNICORN_WORKERS:-1}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
