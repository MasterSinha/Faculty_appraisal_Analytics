import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_journals_analytics_service, require_analytics_role
from app.schemas.journals_analytics import (
    FacultyAnalyticsResponse,
    FacultyJournalDetailResponse,
    OverviewAnalyticsResponse,
    PaginatedDepartmentAnalyticsResponse,
    PaginatedJournalRecordResponse,
    QualityIndexingAnalyticsResponse,
)
from app.services.journals_analytics_service import JournalsAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/journals", tags=["Journal Publications Analytics Module"])


def get_global_filters(
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty_email: Optional[str] = Query(None, description="Faculty email filter"),
    indexing: Optional[str] = Query(None, description="Indexing type filter"),
    journal: Optional[str] = Query(None, description="Journal name filter"),
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
        "indexing": indexing,
        "journal": journal,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }


@router.get("/overview", response_model=OverviewAnalyticsResponse)
def get_overview(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: JournalsAnalyticsService = Depends(get_journals_analytics_service),
):
    """1. Overview KPIs & Summary Statistics for Journal Publications."""
    return service.overview(filters)


@router.get("/departments", response_model=PaginatedDepartmentAnalyticsResponse)
def get_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: JournalsAnalyticsService = Depends(get_journals_analytics_service),
):
    """2. Department-level Analytics with quadrant classification."""
    return service.departments(page, page_size, filters)


@router.get("/faculty", response_model=FacultyAnalyticsResponse)
def get_faculty(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: JournalsAnalyticsService = Depends(get_journals_analytics_service),
):
    """3. Faculty Analytics with performance summary & grouped lists."""
    return service.faculty(page, page_size, filters)


@router.get("/quality-indexing", response_model=QualityIndexingAnalyticsResponse)
def get_quality_indexing(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: JournalsAnalyticsService = Depends(get_journals_analytics_service),
):
    """4. Quality & Indexing breakdown with common journals and duplicate titles."""
    return service.quality_indexing(filters)


@router.get("/records", response_model=PaginatedJournalRecordResponse)
def get_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: JournalsAnalyticsService = Depends(get_journals_analytics_service),
):
    """5. Paginated Journal Publication Records with final_validated_score COALESCE."""
    return service.records(page, page_size, filters)


@router.get("/faculty/{faculty_email}", response_model=FacultyJournalDetailResponse)
def get_faculty_detail(
    faculty_email: str,
    _: dict = Depends(require_analytics_role),
    service: JournalsAnalyticsService = Depends(get_journals_analytics_service),
):
    """6. Detailed Journal Profile for a specific faculty member by email."""
    return service.faculty_detail(faculty_email)


@router.get("/export")
def export_csv(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: JournalsAnalyticsService = Depends(get_journals_analytics_service),
):
    """7. CSV Export matching active filters."""
    rows = service.export_csv_rows(filters)
    output = io.StringIO()
    if rows:
        headers = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = 'attachment; filename="journal_publications_export.csv"'
    return response
