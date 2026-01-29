FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml .

# Create virtual environment and install dependencies
RUN uv venv && uv sync

ENV PYTHONUNBUFFERED=1

COPY . .

EXPOSE 5005

# Run with uv's virtual environment
CMD ["uv", "run", "python", "app/main.py"]
