from fastapi import APIRouter

from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.exports import router as exports_router
from app.api.v1.endpoints.faculty import router as faculty_router

api_v1_router = APIRouter(prefix="/api/v1/research-analytics")
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(faculty_router)
api_v1_router.include_router(exports_router)
