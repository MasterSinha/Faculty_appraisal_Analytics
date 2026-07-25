from fastapi import APIRouter

from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.books import router as books_router
from app.api.v1.endpoints.appraisal_completion_analytics import router as appraisal_completion_analytics_router
from app.api.v1.endpoints.books_analytics import router as books_analytics_router
from app.api.v1.endpoints.conferences_awards_analytics import router as conferences_awards_analytics_router
from app.api.v1.endpoints.department_performance_analytics import router as department_performance_analytics_router
from app.api.v1.endpoints.exports import router as exports_router
from app.api.v1.endpoints.faculty import router as faculty_router
from app.api.v1.endpoints.faculty_performance_analytics import router as faculty_performance_analytics_router
from app.api.v1.endpoints.innovation_pipeline_analytics import router as innovation_pipeline_analytics_router
from app.api.v1.endpoints.journals_analytics import router as journals_analytics_router
from app.api.v1.endpoints.patents_analytics import router as patents_analytics_router
from app.api.v1.endpoints.projects_funding_analytics import router as projects_funding_analytics_router
from app.api.v1.endpoints.research_data_quality_analytics import router as research_data_quality_analytics_router
from app.api.v1.endpoints.school_performance_analytics import router as school_performance_analytics_router
from app.api.v1.endpoints.teaching_research_balance_analytics import router as teaching_research_balance_analytics_router

api_v1_router = APIRouter(prefix="/api/v1/research-analytics")
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(faculty_router)
api_v1_router.include_router(books_router, prefix="/books")
api_v1_router.include_router(exports_router)

# Mount analytics submodules under /api/v1/analytics/*
analytics_v1_router = APIRouter()
analytics_v1_router.include_router(books_analytics_router)
analytics_v1_router.include_router(journals_analytics_router)
analytics_v1_router.include_router(patents_analytics_router)
analytics_v1_router.include_router(projects_funding_analytics_router)
analytics_v1_router.include_router(conferences_awards_analytics_router)
analytics_v1_router.include_router(innovation_pipeline_analytics_router)
analytics_v1_router.include_router(faculty_performance_analytics_router)
analytics_v1_router.include_router(department_performance_analytics_router)
analytics_v1_router.include_router(school_performance_analytics_router)
analytics_v1_router.include_router(teaching_research_balance_analytics_router)
analytics_v1_router.include_router(appraisal_completion_analytics_router)
analytics_v1_router.include_router(research_data_quality_analytics_router)











