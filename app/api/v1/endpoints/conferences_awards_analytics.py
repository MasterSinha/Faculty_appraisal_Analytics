from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_conferences_awards_analytics_service, require_analytics_role
from app.schemas.conferences_awards_analytics import ConferencesAwardsAnalyticsResponse
from app.services.conferences_awards_analytics_service import ConferencesAwardsAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/research", tags=["Conferences & Awards Analytics Module"])


@router.get("/conferences-awards", response_model=ConferencesAwardsAnalyticsResponse)
def get_conferences_awards_analytics(
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty: Optional[str] = Query(None, description="Faculty email or name filter"),
    page_size: Optional[int] = Query(None, ge=1, description="Page size limit for records"),
    _: dict = Depends(require_analytics_role),
    service: ConferencesAwardsAnalyticsService = Depends(get_conferences_awards_analytics_service),
):
    """Retrieve Conferences and Awards Analytics breakdown, department comparison, and faculty details."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "designation": designation,
        "faculty": faculty,
        "page_size": page_size,
    }
    return service.get_analytics(filters)
