FROM python:3.12-slim

# Install necessary tools
RUN apt-get update && apt-get install --no-install-recommends -y \
    iputils-ping \
    curl \
    vim \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# # Install uv and minimal ODBC dependencies in a single layer to keep the image lightweight
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gnupg \
#     unixodbc \
#     && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
#     && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
#     && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
#     && apt-get clean \

# Install UV by copying its binaries from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy only dependency files for caching.
COPY pyproject.toml uv.lock* ./

# Install your project's dependencies using UV.
RUN uv sync --frozen --no-cache --no-dev

# Copy the rest of your application code.
COPY . .

# Ensure any log and asset files (if present) have the proper permissions.
RUN mkdir -p logs && touch logs/app.log && chmod -R 775 logs/app.log

RUN mkdir -p static/resume && chmod -R 775 static/resume

# Expose the port your FastAPI app listens on.
EXPOSE 8000

# (Optional) Uncomment below to switch to a non-root user for enhanced security.
# RUN useradd -m appuser
# USER appuser

# Run the application using the uvicorn executable from the virtual environment.
CMD ["./.venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
