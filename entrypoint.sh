#!/bin/sh
set -e

# Wait for the database to be ready
echo "Waiting for database to be ready..."
while ! nc -z ${POSTGRES_DOCKER_HOST:-postgres} ${POSTGRES_DOCKER_PORT:-5432}; do
  sleep 1
done
echo "Database is ready!"

# Run database migrations
alembic -c alembic.ini upgrade head

# Start the application server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000