from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_school_performance_analytics_service, require_analytics_role
from app.schemas.school_performance_analytics import SchoolPerformanceAnalyticsResponse
from app.services.school_performance_analytics_service import SchoolPerformanceAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/research", tags=["School Performance Analytics Module"])


@router.get("/school-performance", response_model=SchoolPerformanceAnalyticsResponse)
def get_school_performance_analytics(
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(500, ge=1, le=1000, description="Page size limit"),
    sort_by: Optional[str] = Query("total_output", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    search: Optional[str] = Query(None, description="Search query string"),
    _: dict = Depends(require_analytics_role),
    service: SchoolPerformanceAnalyticsService = Depends(get_school_performance_analytics_service),
):
    """Retrieve School Research Performance Analytics including KPI summary, school metrics breakdown, insights, charts, and detail drawer analytics."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "designation": designation,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "search": search,
    }
    return service.get_analytics(page, page_size, filters)
