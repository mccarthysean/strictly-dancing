FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PostgreSQL, PostGIS, and building Python packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies for production)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Run migrations and start server
# Using sh -c to allow running multiple commands
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8001"]
