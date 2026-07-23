# VM Docker Deployment

## Files

- `Dockerfile` builds the FastAPI backend.
- `frontend/Dockerfile` builds the Vite app and serves it with Nginx.
- `frontend/nginx.conf` proxies `/api` and `/health` to FastAPI.
- `docker-compose.yml` runs both services.

## Configure Backend Secrets

Create `Backend/.env` on the VM:

```env
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
JWT_SECRET_KEY=replace_with_secure_secret
ALLOWED_ORIGINS=http://YOUR_VM_IP_OR_DOMAIN
```

Do not put `DATABASE_URL` in the frontend `.env`.

## Deploy

From the `Backend` directory:

```bash
docker compose up -d --build
```

Open:

```text
http://YOUR_VM_IP_OR_DOMAIN/admin/research-analytics
```

The React app is served by Nginx on port `80`. API calls go to the same origin at `/api/v1/research-analytics` and are proxied internally to FastAPI.

## Useful Commands

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose ps
docker compose restart
docker compose down
```

## Verify

```bash
curl http://YOUR_VM_IP_OR_DOMAIN/health
```

Authenticated analytics endpoints require a valid JWT:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://YOUR_VM_IP_OR_DOMAIN/api/v1/research-analytics/overview
```
