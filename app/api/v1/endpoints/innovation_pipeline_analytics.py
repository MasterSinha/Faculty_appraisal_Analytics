from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_innovation_pipeline_analytics_service, require_analytics_role
from app.schemas.innovation_pipeline_analytics import InnovationPipelineAnalyticsResponse
from app.services.innovation_pipeline_analytics_service import InnovationPipelineAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/research", tags=["Innovation Pipeline Analytics Module"])


@router.get("/innovation-pipeline", response_model=InnovationPipelineAnalyticsResponse)
def get_innovation_pipeline_analytics(
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty: Optional[str] = Query(None, description="Faculty email or name filter"),
    page_size: Optional[int] = Query(None, ge=1, description="Page size limit for records"),
    _: dict = Depends(require_analytics_role),
    service: InnovationPipelineAnalyticsService = Depends(get_innovation_pipeline_analytics_service),
):
    """Retrieve Innovation Pipeline Analytics breakdown, funnel stages, contributions, and gap analytics."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "designation": designation,
        "faculty": faculty,
        "page_size": page_size,
    }
    return service.get_analytics(filters)
