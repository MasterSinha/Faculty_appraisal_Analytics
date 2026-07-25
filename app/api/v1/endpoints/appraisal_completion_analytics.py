from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_appraisal_completion_analytics_service, require_analytics_role
from app.schemas.appraisal_completion_analytics import AppraisalCompletionAnalyticsResponse
from app.services.appraisal_completion_analytics_service import AppraisalCompletionAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/research", tags=["Appraisal Completion Analytics Module"])


@router.get("/appraisal-completion", response_model=AppraisalCompletionAnalyticsResponse)
def get_appraisal_completion_analytics(
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty: Optional[str] = Query(None, description="Faculty email or name filter"),
    page_size: Optional[int] = Query(None, ge=1, description="Page size limit"),
    _: dict = Depends(require_analytics_role),
    service: AppraisalCompletionAnalyticsService = Depends(get_appraisal_completion_analytics_service),
):
    """Retrieve Appraisal Completion Analytics breakdown, status analytics, department metrics, follow-up tables, and charts."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "designation": designation,
        "faculty": faculty,
        "page_size": page_size,
    }
    return service.get_analytics(filters)
