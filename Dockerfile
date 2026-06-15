# Multi-stage build for production-ready deployment

# Stage 1: Base image with Python and system dependencies
FROM python:3.10-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Development stage with all dependencies
FROM base as development

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 3000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production stage (optimized)
FROM base as production

COPY requirements.txt .

# Install only production dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
