# Backend Dockerfile (Django) - Python slim
FROM python:3.11-slim AS base

# Prevents Python from writing pyc files and enables unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps required to build mysqlclient and runtime libs
# - build-essential provides gcc and build tools
# - default-libmysqlclient-dev provides MySQL headers
# - netcat-openbsd used by entrypoint to wait for DB
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       default-libmysqlclient-dev \
       pkg-config \
       netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . /app

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Default command uses entrypoint that waits for DB, runs migrations and starts server
CMD ["/app/entrypoint.sh"]
