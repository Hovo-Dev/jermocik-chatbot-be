FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    git \
    curl \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip (more reliable)
RUN pip install uv

# Copy uv configuration files first for better caching
COPY pyproject.toml README.md uv.lock ./

# Install Python dependencies using uv (production with psycopg2 source)
RUN uv sync --frozen --extra prod

# Copy project
COPY . /app/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Collect static files
RUN uv run python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Default command
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "django_api_project.wsgi:application"]
