from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_faculty_performance_analytics_service, require_analytics_role
from app.schemas.faculty_performance_analytics import FacultyPerformanceAnalyticsResponse
from app.services.faculty_performance_analytics_service import FacultyPerformanceAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/research", tags=["Faculty Performance Analytics Module"])


@router.get("/faculty-performance", response_model=FacultyPerformanceAnalyticsResponse)
def get_faculty_performance_analytics(
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty: Optional[str] = Query(None, description="Faculty email or name filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(500, ge=1, le=1000, description="Page size limit"),
    sort_by: Optional[str] = Query("validated_research_score", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    search: Optional[str] = Query(None, description="Search query string"),
    _: dict = Depends(require_analytics_role),
    service: FacultyPerformanceAnalyticsService = Depends(get_faculty_performance_analytics_service),
):
    """Retrieve Faculty Research Performance Analytics with metrics across all 11 activity categories, segments, charts, and drawer details."""
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
