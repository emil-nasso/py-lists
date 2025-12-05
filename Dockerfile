# Multi-stage build to reduce final image size
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv and sync dependencies
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev

# Final stage - only runtime needs
FROM python:3.12-slim

WORKDIR /app

# Copy only the virtual environment and app code
COPY --from=builder /app/.venv /app/.venv
COPY ./app ./app

# Runtime optimizations for memory efficiency
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Single worker = minimum memory (~80-120MB total)
# Use --limit-concurrency to handle load without additional workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "50"]
