#!/usr/bin/env bash
set -euo pipefail

# Wait for MySQL to be ready, if DB_HOST and DB_PORT are set
if [[ -n "${DB_HOST:-}" ]]; then
  echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT:-3306}..."
  until nc -z ${DB_HOST} ${DB_PORT:-3306}; do
    sleep 1
  done
  echo "MySQL is up!"
fi

# Apply migrations
python manage.py migrate --noinput

# Optionally seed demo data
if [[ "${SEED_DATA:-1}" == "1" ]]; then
  echo "Seeding demo products..."
  python manage.py shell -c "from chat.seed import seed_products; seed_products()" || true
fi

# Collect static files (noop for dev)
python manage.py collectstatic --noinput || true

# Start server
if [[ "${DJANGO_DEBUG:-True}" =~ ^(1|true|True|on|yes)$ ]]; then
  echo "Starting Django dev server..."
  python manage.py runserver 0.0.0.0:8000
else
  echo "Starting Gunicorn..."
  exec gunicorn mysite.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-3} \
    --timeout ${GUNICORN_TIMEOUT:-60}
fi
