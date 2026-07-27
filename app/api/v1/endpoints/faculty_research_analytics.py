import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import text

from app.api.deps import get_faculty_research_analytics_service, require_analytics_role
from app.core.cache import (
    clear_cache,
    get_cache_stats,
    get_health_stats,
    update_last_refresh_timestamp,
)
from app.schemas.faculty_research_analytics import DashboardResponse, HealthResponse, InsightResponse, PaginatedResponse, ResearchOverview
from app.services.faculty_research_analytics_service import FacultyResearchAnalyticsService
from app.utils.export_utils import rows_to_csv


router = APIRouter(prefix="/api/v1/analytics/research", tags=["Faculty Research Analytics"])


def clean_filter(value: Optional[str]) -> Optional[str]:
    """Server-side filter sanitizer to ensure default 'All ...' filters map to None (unfiltered)."""
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    val_lower = val_str.lower()
    if val_lower in {
        "all", "none", "null", "undefined", "",
        "all schools", "all departments", "all years",
        "all designations", "all categories", "all indexing"
    }:
        return None
    if val_lower.startswith("all "):
        return None
    return val_str


def query_filters(
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Designation filter"),
    faculty: Optional[str] = Query(None, description="Faculty email or search name"),
    category: Optional[str] = Query(None, description="Research category filter"),
    indexing: Optional[str] = Query(None, description="Indexing filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    agency: Optional[str] = Query(None, description="Agency filter"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: Optional[str] = Query(None, description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    date_from: Optional[str] = Query(None, description="Date from"),
    date_to: Optional[str] = Query(None, description="Date to"),
) -> dict[str, Any]:
    return {
        "academic_year": clean_filter(academic_year),
        "school": clean_filter(school),
        "department": clean_filter(department),
        "designation": clean_filter(designation),
        "faculty_email": clean_filter(faculty),
        "faculty": clean_filter(faculty),
        "category": clean_filter(category),
        "indexing": clean_filter(indexing),
        "status": clean_filter(status),
        "agency": clean_filter(agency),
        "search": clean_filter(search),
        "sort_by": clean_filter(sort_by),
        "sort_order": sort_order,
        "date_from": clean_filter(date_from),
        "date_to": clean_filter(date_to),
    }


# -----------------------------------------------------------------------------
# 1. FAST DASHBOARD SUMMARY ENDPOINT
# -----------------------------------------------------------------------------
@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    refresh: bool = Query(False, description="Bypass cache and rebuild analytics payload"),
    filters: dict[str, Any] = Depends(query_filters),
    _: dict = Depends(require_analytics_role),
    service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service),
):
    """Single fast dashboard summary endpoint returning all first-screen data in one response."""
    return service.dashboard_summary(filters, refresh=refresh)


# -----------------------------------------------------------------------------
# 2. HEALTH & DEBUG ENDPOINTS
# -----------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse)
def health_status(
    service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service),
):
    """Analytics microservice health and cache status check."""
    db_status = "connected"
    try:
        service.repository.db.execute(text("SELECT 1")).scalar()
    except Exception as e:
        db_status = f"error: {str(e)}"

    c_stats = get_cache_stats()
    h_stats = get_health_stats()

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "cache": "enabled" if c_stats["active_in_memory_keys"] >= 0 else "disabled",
        "dashboard_cache_keys": c_stats["active_in_memory_keys"],
        "slowest_recent_endpoint": h_stats.get("slowest_recent_endpoint") or "none",
        "last_materialized_view_refresh": h_stats.get("last_materialized_view_refresh") or "none",
    }


@router.get("/debug-counts")
def debug_counts(
    metric: str = Query("patents", description="Metric to inspect: patents, journals, books, projects"),
    service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service),
):
    """Debug endpoint verifying consistency between All Schools total and individual school counts."""
    return service.repository.debug_counts(metric)


@router.post("/refresh-materialized-views", status_code=status.HTTP_200_OK)
def refresh_materialized_views(
    _: dict = Depends(require_analytics_role),
    service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service),
):
    """Safely refresh PostgreSQL materialized views and flush analytics cache."""
    now_str = datetime.datetime.now().astimezone().isoformat()
    refreshed_views = []
    errors = []

    mviews = [
        "mv_research_faculty_summary",
        "mv_research_department_summary",
        "mv_research_school_summary",
        "mv_research_yearly_trend",
        "mv_research_category_summary",
        "mv_research_data_quality_summary",
        "mv_research_filter_options",
    ]

    for mv in mviews:
        try:
            service.repository.db.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv}"))
            service.repository.db.commit()
            refreshed_views.append(mv)
        except Exception:
            service.repository.db.rollback()
            try:
                service.repository.db.execute(text(f"REFRESH MATERIALIZED VIEW {mv}"))
                service.repository.db.commit()
                refreshed_views.append(mv)
            except Exception as ex:
                service.repository.db.rollback()
                errors.append(f"{mv}: {str(ex)}")

    cleared = clear_cache()
    update_last_refresh_timestamp(now_str)

    return {
        "status": "completed" if not errors else "partial_success",
        "refreshed_materialized_views": refreshed_views,
        "errors": errors,
        "cache_entries_cleared": cleared,
        "timestamp": now_str,
    }


# -----------------------------------------------------------------------------
# 3. DETAILED ENDPOINTS (WITH PRE-PAGINATION SUMMARY METRICS)
# -----------------------------------------------------------------------------
@router.get("/overview", response_model=ResearchOverview)
def overview(filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.overview(filters)


@router.get("/departments", response_model=PaginatedResponse)
def departments(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.departments(filters, page, page_size)


@router.get("/schools", response_model=PaginatedResponse)
def schools(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.schools(filters, page, page_size)


@router.get("/faculty", response_model=PaginatedResponse)
def faculty(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.faculty(filters, page, page_size)


@router.get("/faculty/{faculty_email}")
def faculty_detail(faculty_email: str, filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.faculty_detail(faculty_email, filters)


@router.get("/publications", response_model=PaginatedResponse)
def publications(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("journal_publications", filters, page, page_size)


@router.get("/books", response_model=PaginatedResponse)
def books(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("book_publications", filters, page, page_size)


@router.get("/patents", response_model=PaginatedResponse)
def patents(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("patents", filters, page, page_size)


@router.get("/projects", response_model=PaginatedResponse)
def projects(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("research_projects", filters, page, page_size)


@router.get("/funding")
def funding(filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    overview_data = service.overview(filters)
    return {"total_sanctioned_funding": overview_data["total_sanctioned_funding"], "external_funded_amount": overview_data["external_funded_amount"], "funding_per_active_faculty": overview_data["funding_per_active_faculty"]}


@router.get("/guidance", response_model=PaginatedResponse)
def guidance(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("research_guidance", filters, page, page_size)


@router.get("/trends")
def trends(filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.trends(filters)


@router.get("/insights", response_model=InsightResponse)
def insights(filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.insights(filters)


@router.get("/data-quality")
def data_quality(filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.data_quality(filters)


@router.get("/filters")
def filters(_: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.filters()


@router.get("/export")
def export(filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    rows = service.faculty(filters, 1, 10000)["items"]
    return Response(content=rows_to_csv(rows), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=faculty-research-analytics.csv"})
