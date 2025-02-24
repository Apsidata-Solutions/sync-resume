# ------------------------- Builder Stage -------------------------

FROM python:3.12-slim AS builder

# (Optional) Install build tools if needed for compiling any dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV by copying its binaries from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy only dependency files for caching.
COPY pyproject.toml uv.lock* ./

# Install your project's dependencies using UV.
RUN uv sync --frozen --no-cache

# Copy the rest of your application code.
COPY . .


# ------------------------- Runner Stage -------------------------
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy the built virtual environment and application source from the builder.
COPY --from=builder /app /app

# Ensure any log files (if present) have the proper permissions.
RUN mkdir -p logs && touch logs/app.log && chmod -R 775 logs/app.log

# Expose the port your FastAPI app listens on.
EXPOSE 8000

# (Optional) Uncomment below to switch to a non-root user for enhanced security.
# RUN useradd -m appuser
# USER appuser

# Run the application using the uvicorn executable from the virtual environment.
CMD ["./.venv/bin/uvicorn", "src.backend:app", "--host", "0.0.0.0", "--port", "8000"]
