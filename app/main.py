from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Faculty Appraisal Research Analytics",
    description="Production API microservice providing research performance, publications, funding, and appraisal analytics.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint for container monitoring and load balancers."""
    return {"status": "ok", "version": "2.0.0"}


# Serve compiled React SPA bundle if dist directory exists
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
analytics_base_path = "/Analytics"

if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        app.mount(f"{analytics_base_path}/assets", StaticFiles(directory=assets_dir), name="analytics-assets")

    @app.get(f"{analytics_base_path}", include_in_schema=False)
    @app.get(f"{analytics_base_path}/", include_in_schema=False)
    @app.get(f"{analytics_base_path}/admin/research-analytics", include_in_schema=False)
    @app.get("/admin/research-analytics", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    def serve_research_dashboard():
        return FileResponse(frontend_dist / "index.html")

    @app.get(f"{analytics_base_path}/{{full_path:path}}", include_in_schema=False)
    def serve_analytics_fallback(full_path: str):
        requested_file = frontend_dist / full_path
        if requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_fallback(full_path: str):
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        requested_file = frontend_dist / full_path
        if requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(frontend_dist / "index.html")
