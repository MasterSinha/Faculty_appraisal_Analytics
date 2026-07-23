from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

