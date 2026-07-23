from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.research_analytics import router as research_analytics_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(title="Faculty Appraisal Research Analytics", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_analytics_router)


@app.get("/health")
def health():
    return {"status": "ok"}


frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/admin/research-analytics", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    def serve_research_dashboard():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_fallback(full_path: str):
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        requested_file = frontend_dist / full_path
        if requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(frontend_dist / "index.html")
