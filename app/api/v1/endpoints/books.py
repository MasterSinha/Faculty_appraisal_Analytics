from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_books_analytics_service, require_analytics_role
from app.schemas.books import (
    BookChartsResponse,
    BookKpiResponse,
    BookQuadrantItem,
    IndexRecommendationResponse,
    PaginatedBookResponse,
)
from app.services.books_analytics_service import BooksAnalyticsService

router = APIRouter(tags=["Books Analytics"])


@router.get("/summary", response_model=BookKpiResponse)
def get_books_summary(
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """Retrieve primary Book & Chapter KPIs (Total Books, Participation Rate, ISBN count, Author Roles)."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
    }
    return service.get_books_kpis(filters)


@router.get("/charts", response_model=BookChartsResponse)
def get_books_charts(
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """Retrieve books breakdowns by department, publisher, role, and academic year."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
    }
    return service.get_books_charts(filters)


@router.get("/quadrant", response_model=list[BookQuadrantItem])
def get_books_quadrant(
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """Retrieve Quadrant Scatter comparison data (X: Participation Rate %, Y: Books per Active Faculty)."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
    }
    return service.get_books_quadrant(filters)


@router.get("/list", response_model=PaginatedBookResponse)
def get_books_table(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    search: Optional[str] = Query(None, description="Search term across title, faculty name, publisher, ISBN"),
    sort_by: str = Query("book_title", description="Field to sort by"),
    sort_order: str = Query("desc", description="asc or desc"),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """Retrieve paginated detailed book and chapter publication records."""
    filters = {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    return service.get_books_table(page, page_size, filters)


@router.get("/indexes", response_model=IndexRecommendationResponse)
def get_index_recommendations(
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """Retrieve DBA index recommendations for optimizing Books Analytics queries."""
    return {"recommended_indexes": service.get_index_recommendations()}
