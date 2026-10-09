# ==============================================================================
# Multi-stage Dockerfile for LeadQualify AI (Frontend + Backend Unified Service)
# ==============================================================================

# Stage 1: Build Next.js Static Web Application
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime with FastAPI serving both API & UI
FROM python:3.10-slim AS runner
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy compiled frontend static assets from Stage 1 into frontend/out
COPY --from=frontend-builder /app/frontend/out ./frontend/out

ENV PYTHONPATH=/app/backend
ENV PORT=10000

EXPOSE 10000

# Start Uvicorn on Render dynamic PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
