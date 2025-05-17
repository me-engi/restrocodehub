# --- Stage 1: Builder Stage ---
FROM python:3.11-slim as builder

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies for building wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        libjpeg62-turbo-dev \
        zlib1g-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/wheels

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Build wheels for all dependencies
RUN pip wheel --no-cache-dir --wheel-dir=/opt/wheels -r requirements.txt


# --- Stage 2: Runtime Stage ---
FROM python:3.11-slim

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=culinary_api.settings

# Create non-root user
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libmysqlclient21 \
        libjpeg62-turbo \
        zlib1g \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

# Copy wheels from builder stage
COPY --from=builder --chown=appuser:appuser /opt/wheels /wheels

# Install dependencies from local wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Create directories for static and media files
RUN mkdir -p /opt/app/staticfiles && \
    mkdir -p /opt/app/media && \
    chown -R appuser:appuser /opt/app/staticfiles /opt/app/media

# Ensure entrypoint is executable
RUN chmod +x ./docker-entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8000

ENTRYPOINT ["/opt/app/docker-entrypoint.sh"]