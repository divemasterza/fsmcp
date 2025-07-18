# syntax=docker/dockerfile:1.4

# Stage 1: Builder - Build the wheel package
FROM python:3.12-slim-bookworm as builder

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set working directory
WORKDIR /app

# Copy project metadata and source code early
COPY pyproject.toml ./
COPY README.md ./
COPY nextcloud_mcp/ ./nextcloud_mcp/
COPY api.py ./api.py

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip and hatch to build the package
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir hatch

# Build the package (hatch builds both sdist and wheel by default)
RUN hatch build

# Stage 2: Runner - Create the final runtime image
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set working directory
WORKDIR /app

# Copy only the built wheel from the builder stage
COPY --from=builder /app/dist/*.whl ./

# Copy application source code
COPY nextcloud_mcp/ ./nextcloud_mcp/
COPY api.py ./api.py

# Install the built wheel and its runtime dependencies
# The wheel contains the project's runtime dependencies defined in pyproject.toml
RUN pip install --no-cache-dir *.whl

# Expose the port Uvicorn will run on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
