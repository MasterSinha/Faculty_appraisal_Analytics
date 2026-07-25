from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_teaching_research_balance_analytics_service, require_analytics_role
from app.schemas.teaching_research_balance_analytics import TeachingResearchBalanceAnalyticsResponse
from app.services.teaching_research_balance_analytics_service import TeachingResearchBalanceAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/research", tags=["Teaching vs Research Analytics Module"])


@router.get("/teaching-research-balance", response_model=TeachingResearchBalanceAnalyticsResponse)
def get_teaching_research_balance_analytics(
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty: Optional[str] = Query(None, description="Faculty email or name filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(500, ge=1, le=1000, description="Page size limit"),
    sort_by: Optional[str] = Query("teaching_score_percentage", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    search: Optional[str] = Query(None, description="Search query string"),
    _: dict = Depends(require_analytics_role),
    service: TeachingResearchBalanceAnalyticsService = Depends(get_teaching_research_balance_analytics_service),
):
    """Retrieve Teaching vs Research Analytics including normalized score percentages, 4-quadrant classification, department balance, component breakdowns, and trends."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "designation": designation,
        "faculty": faculty,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "search": search,
    }
    return service.get_analytics(page, page_size, filters)
