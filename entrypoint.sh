#!/bin/sh
set -e

# Run database migrations
alembic -c alembic.ini upgrade head

# Start the application server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
