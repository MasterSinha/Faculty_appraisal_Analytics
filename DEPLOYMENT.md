# VM Docker Deployment

This project now uses one production Docker image:

- Stage 1 builds the React dashboard from `frontend/`.
- Stage 2 runs FastAPI with Gunicorn/Uvicorn.
- The compiled React bundle is copied into `frontend/dist`.
- FastAPI serves `/admin/research-analytics` and proxies no database secrets to the browser.

## Environment

Create `Backend/.env` on the VM:

```env
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
JWT_SECRET_KEY=replace_with_secure_secret
ALLOWED_ORIGINS=http://YOUR_VM_IP_OR_DOMAIN:8080
```

Do not put `DATABASE_URL` in any frontend env file.

## Build And Run

From the `Backend` directory:

```bash
docker compose up -d --build
```

Open:

```text
http://YOUR_VM_IP_OR_DOMAIN:8080/Analytics
```

Health check:

```bash
curl http://YOUR_VM_IP_OR_DOMAIN:8080/health
```

Authenticated API example:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://YOUR_VM_IP_OR_DOMAIN:8080/api/v1/research-analytics/overview
```

## Useful Commands

```bash
docker compose logs -f
docker compose ps
docker compose restart
docker compose down
```

## Direct Docker Commands

```bash
docker build -t faculty-analytics .
docker run --env-file .env -p 8080:8080 faculty-analytics
```
