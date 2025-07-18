# syntax=docker/dockerfile:1.4

# Stage 1: Build the application
FROM python:3.12-slim-bookworm as builder

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY nextcloud_mcp/ ./nextcloud_mcp/
COPY api.py ./api.py

# Install Python dependencies using pip (assuming pyproject.toml for dependencies)
# We install in editable mode to ensure local package is found
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -e .[test] # Install core and test dependencies

# Stage 2: Create the final runtime image
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set working directory
WORKDIR /app

# Copy only necessary files from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app/nextcloud_mcp /app/nextcloud_mcp
COPY --from=builder /app/api.py /app/api.py

# Expose the port Uvicorn will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]