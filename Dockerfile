FROM python:3.12
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Copy application code
COPY . .

# Create entrypoint script directly in Dockerfile
RUN printf '#!/bin/sh\n\
set -e\n\
\n\
echo "Waiting for database..."\n\
while ! nc -z ${POSTGRES_DOCKER_HOST:-postgres} ${POSTGRES_DOCKER_PORT:-5432}; do\n\
  sleep 1\n\
done\n\
echo "Database ready!"\n\
\n\
alembic -c alembic.ini upgrade head\n\
\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000\n' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]