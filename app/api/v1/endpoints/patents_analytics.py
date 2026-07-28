import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_patents_analytics_service, require_analytics_role
from app.schemas.patents_analytics import (
    OverviewPatentsResponse,
    PaginatedDepartmentPatentResponse,
    PaginatedFacultyPatentResponse,
    PaginatedIPRRecordResponse,
    PaginatedPatentRecordResponse,
    PatentStatusAnalyticsResponse,
    TrendAnalyticsResponse,
)
from app.services.patents_analytics_service import PatentsAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/patents-ipr", tags=["Patents & IPR Analytics Module"])


def get_global_filters(
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty_email: Optional[str] = Query(None, description="Faculty email filter"),
    status: Optional[str] = Query(None, description="Status filter (Granted, Filed, Pending, etc.)"),
    scope: Optional[str] = Query(None, description="Scope filter (Domestic, International)"),
    date_from: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search term filter"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
) -> dict:
    return {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "designation": designation,
        "faculty_email": faculty_email,
        "status": status,
        "scope": scope,
        "date_from": date_from,
        "date_to": date_to,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }


@router.get("/overview", response_model=OverviewPatentsResponse)
def get_overview(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: PatentsAnalyticsService = Depends(get_patents_analytics_service),
):
    """1. Overview KPIs & Summary Statistics for Patents and IPR."""
    return service.overview(filters)


@router.get("/status", response_model=PatentStatusAnalyticsResponse)
def get_status_analytics(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: PatentsAnalyticsService = Depends(get_patents_analytics_service),
):
    """2. Status & Scope distributions, school shares, and data quality metrics."""
    return service.status_analytics(filters)


@router.get("/departments", response_model=PaginatedDepartmentPatentResponse)
def get_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: PatentsAnalyticsService = Depends(get_patents_analytics_service),
):
    """3. Department-level Analytics for Patents and IPR."""
    return service.departments(page, page_size, filters)


@router.get("/faculty", response_model=PaginatedFacultyPatentResponse)
def get_faculty(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: PatentsAnalyticsService = Depends(get_patents_analytics_service),
):
    """4. Faculty-level Patent & IPR summary analytics."""
    return service.faculty(page, page_size, filters)


@router.get("/records/patents", response_model=PaginatedPatentRecordResponse)
def get_records_patents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    view: str = Query("grouped", description="View mode: grouped or raw"),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: PatentsAnalyticsService = Depends(get_patents_analytics_service),
):
    """5. Paginated Patent Records with final_validated_score COALESCE."""
    filters = {**filters, "view": view}
    return service.records_patents(page, page_size, filters)


@router.get("/records/ipr", response_model=PaginatedIPRRecordResponse)
def get_records_ipr(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: PatentsAnalyticsService = Depends(get_patents_analytics_service),
):
    """6. Paginated IPR Records."""
    return service.records_ipr(page, page_size, filters)


@router.get("/trends", response_model=TrendAnalyticsResponse)
def get_trends(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: PatentsAnalyticsService = Depends(get_patents_analytics_service),
):
    """7. Annual trends and Year-over-Year growth analytics."""
    return service.trends(filters)


@router.get("/export")
def export_csv(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: PatentsAnalyticsService = Depends(get_patents_analytics_service),
):
    """8. CSV Export matching active filters."""
    rows = service.export_csv_rows(filters)
    output = io.StringIO()
    if rows:
        headers = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = 'attachment; filename="patents_ipr_analytics_export.csv"'
    return response
