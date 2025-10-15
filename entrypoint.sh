#!/usr/bin/env sh
set -e

if [ "$DB_ENGINE" = "postgres" ]; then
  echo "Waiting for Postgres..."
  until python -c "import sys,psycopg2; import os; psycopg2.connect(dbname=os.getenv('POSTGRES_DB','movos'), user=os.getenv('POSTGRES_USER','movos'), password=os.getenv('POSTGRES_PASSWORD','movos'), host=os.getenv('POSTGRES_HOST','db'), port=int(os.getenv('POSTGRES_PORT','5432')))"; do
    echo "Postgres is unavailable - sleeping"
    sleep 2
  done
fi

echo "Running migrations"
python manage.py migrate --noinput

echo "Collecting static files"
python manage.py collectstatic --noinput || true

exec "$@"
