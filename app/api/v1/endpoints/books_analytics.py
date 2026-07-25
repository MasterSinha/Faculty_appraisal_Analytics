import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_books_analytics_service, require_analytics_role
from app.schemas.books_analytics import (
    AuthorshipAnalyticsResponse,
    BookOverviewResponse,
    FacultyBookDetailResponse,
    PaginatedBookRecordResponse,
    PaginatedDepartmentBookResponse,
    PublisherAnalyticsItem,
    QualityAnalyticsResponse,
)
from app.services.books_analytics_service import BooksAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/books", tags=["Books Analytics Module"])


def get_global_filters(
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty_email: Optional[str] = Query(None, description="Faculty email filter"),
    publisher: Optional[str] = Query(None, description="Publisher name filter"),
    isbn_status: Optional[str] = Query(None, description="with_isbn, missing_isbn, or duplicate_isbn"),
    authorship_type: Optional[str] = Query(None, description="first_author, coauthored, or unspecified"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: Optional[str] = Query("title", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
) -> dict:
    return {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "designation": designation,
        "faculty_email": faculty_email,
        "publisher": publisher,
        "isbn_status": isbn_status,
        "authorship_type": authorship_type,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }


@router.get("/overview", response_model=BookOverviewResponse)
def get_overview(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """1. Overview KPIs & Summary Statistics."""
    return service.overview(filters)


@router.get("/departments", response_model=PaginatedDepartmentBookResponse)
def get_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """2. Department-level Analytics with pagination and sorting."""
    return service.departments(page, page_size, filters)


@router.get("/publishers", response_model=list[PublisherAnalyticsItem])
def get_publishers(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """3. Publisher Analytics sorted by total_books descending."""
    return service.publishers(filters)


@router.get("/authorship", response_model=AuthorshipAnalyticsResponse)
def get_authorship(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """4. Authorship & Collaboration Analytics."""
    return service.authorship(filters)


@router.get("/quality", response_model=QualityAnalyticsResponse)
def get_quality(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """5. Data Quality & Verification Analytics."""
    return service.quality(filters)


@router.get("/records", response_model=PaginatedBookRecordResponse)
def get_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """6. Paginated Book Publication Records with final_validated_score COALESCE."""
    return service.records(page, page_size, filters)


@router.get("/faculty/{faculty_email}", response_model=FacultyBookDetailResponse)
def get_faculty_detail(
    faculty_email: str,
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
):
    """7. Detailed Books Analytics for one faculty member."""
    return service.faculty_detail(faculty_email)


@router.get("/export")
def export_csv(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: BooksAnalyticsService = Depends(get_books_analytics_service),
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
    response.headers["Content-Disposition"] = 'attachment; filename="books_analytics_export.csv"'
    return response
