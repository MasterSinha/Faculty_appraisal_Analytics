import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints.faculty_research_analytics import router as faculty_research_analytics_router
from app.api.v1.router import analytics_v1_router, api_v1_router
from app.core.config import get_settings
from app.database import SessionLocal
from app.repositories.faculty_research_analytics_repository import FacultyResearchAnalyticsRepository

logger = logging.getLogger("analytics.main")
settings = get_settings()

app = FastAPI(
    title="Faculty Appraisal Research Analytics",
    description="Production API microservice providing research performance, publications, funding, and appraisal analytics.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. GZip Compression Middleware (Compresses ~40KB JSON down to ~3KB over network)
app.add_middleware(GZipMiddleware, minimum_size=500)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)
app.include_router(analytics_v1_router)
app.include_router(faculty_research_analytics_router)


# 3. Server Startup Event: Background Pre-Warming of Cache
@app.on_event("startup")
def prewarm_analytics_cache():
    """Background startup task to pre-warm dashboard cache so users get instant sub-5ms load times."""
    def _warm():
        try:
            db = SessionLocal()
            try:
                repo = FacultyResearchAnalyticsRepository(db)
                repo.dashboard_summary({}, refresh=True)
                repo.filters()
                logger.info("[startup] Successfully pre-warmed dashboard & filters cache!")
            finally:
                db.close()
        except Exception as e:
            logger.warning("[startup] Cache pre-warming warning: %s", e)

    # Run in background thread so server start is non-blocking
    asyncio.get_event_loop().run_in_executor(None, _warm)


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint for container monitoring and load balancers."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/", include_in_schema=False)
def root():
    """Root endpoint returning API status instead of rendering the frontend."""
    return {
        "message": "Faculty Appraisal Research Analytics API",
        "status": "running",
        "docs": "/docs",
        "analytics_dashboard": "/Analytics",
    }


# Serve compiled React SPA bundle strictly under /Analytics
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
    def serve_research_dashboard():
        return FileResponse(frontend_dist / "index.html")

    @app.get(f"{analytics_base_path}/{{full_path:path}}", include_in_schema=False)
    def serve_analytics_fallback(full_path: str):
        requested_file = frontend_dist / full_path
        if requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(frontend_dist / "index.html")
