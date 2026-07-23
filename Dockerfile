# =============================================================================
# Stage 1 - Build the React frontend
# =============================================================================
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

# Install deps first so Docker can cache npm install unless package files change.
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts

COPY frontend/ ./
ARG VITE_API_BASE_URL=""
ARG VITE_BASE_PATH="/Analytics/"
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH
RUN npm run build

# =============================================================================
# Stage 2 - Python / FastAPI backend
# =============================================================================
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV WORKERS=2

# Install PostgreSQL client 16 from the official PostgreSQL repository.
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates lsb-release gnupg \
  && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
    > /etc/apt/sources.list.d/pgdg.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends postgresql-client-16 \
  && apt-get purge -y --auto-remove curl ca-certificates lsb-release gnupg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Overlay the compiled React bundle so FastAPI can serve it.
COPY --from=frontend-build /frontend/dist ./frontend/dist

EXPOSE 8080

CMD ["sh", "-c", "gunicorn -w ${WORKERS:-2} -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT:-8080} --timeout 0"]
