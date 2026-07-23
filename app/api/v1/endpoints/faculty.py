from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_analytics_service, require_analytics_role
from app.schemas.faculty import FacultyDetailResponse, PaginatedFacultyResponse
from app.services.research_analytics_service import ResearchAnalyticsService

router = APIRouter(tags=["Faculty Analytics"])


@router.get("/faculty", response_model=PaginatedFacultyResponse)
def get_faculty_summary(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    school: Optional[str] = None,
    department: Optional[str] = None,
    indexing: Optional[str] = None,
    year: Optional[int] = None,
    sort_by: str = "total_research_papers",
    sort_order: Literal["asc", "desc"] = "desc",
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve paginated, filtered faculty research summaries."""
    filters = {
        "search": search,
        "school": school,
        "department": department,
        "indexing": indexing,
        "year": year,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    return service.faculty_summary(page, page_size, filters)


@router.get("/faculty/{faculty_id}")
def get_faculty_detail(
    faculty_id: str,
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve comprehensive research details and records for a specific faculty member."""
    return service.faculty_detail(faculty_id)


@router.get("/top-faculty")
def top_faculty(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve top performing faculty ranked by research activity."""
    return {"data": service.top_faculty(limit)}
