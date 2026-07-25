import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_projects_funding_analytics_service, require_analytics_role
from app.schemas.projects_funding_analytics import (
    ConcentrationAnalyticsResponse,
    FundingAgencyItem,
    OverviewProjectsFundingResponse,
    PaginatedDepartmentFundingResponse,
    PaginatedFacultyFundingResponse,
    PaginatedProjectRecordResponse,
    PaginatedProposalRecordResponse,
    TrendAnalyticsResponse,
)
from app.services.projects_funding_analytics_service import ProjectsFundingAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/projects-funding", tags=["Projects & Funding Analytics Module"])


def get_global_filters(
    academic_year: Optional[str] = Query(None, description="Academic year filter"),
    school: Optional[str] = Query(None, description="School filter"),
    department: Optional[str] = Query(None, description="Department filter"),
    designation: Optional[str] = Query(None, description="Faculty designation filter"),
    faculty_email: Optional[str] = Query(None, description="Faculty email filter"),
    agency: Optional[str] = Query(None, description="Funding agency filter"),
    project_status: Optional[str] = Query(None, description="Project status filter"),
    role: Optional[str] = Query(None, description="Investigator role filter"),
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
        "agency": agency,
        "project_status": project_status,
        "role": role,
        "date_from": date_from,
        "date_to": date_to,
        "search": search,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }


@router.get("/overview", response_model=OverviewProjectsFundingResponse)
def get_overview(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """1. Overview KPIs & Summary Statistics for Projects and Funding."""
    return service.overview(filters)


@router.get("/projects", response_model=PaginatedProjectRecordResponse)
def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """2. Paginated Internal Research Project Records."""
    return service.projects(page, page_size, filters)


@router.get("/external-projects", response_model=PaginatedProjectRecordResponse)
def get_external_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """3. Paginated External Research Project Records."""
    return service.external_projects(page, page_size, filters)


@router.get("/proposals", response_model=PaginatedProposalRecordResponse)
def get_proposals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """4. Paginated Research Proposal Records."""
    return service.proposals(page, page_size, filters)


@router.get("/funding-agencies", response_model=List[FundingAgencyItem])
def get_funding_agencies(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """5. Funding Agencies Analytics."""
    return service.funding_agencies(filters)


@router.get("/departments", response_model=PaginatedDepartmentFundingResponse)
def get_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """6. Department-level Projects & Funding Analytics."""
    return service.departments(page, page_size, filters)


@router.get("/faculty", response_model=PaginatedFacultyFundingResponse)
def get_faculty(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """7. Faculty-level Funding & Proposal Analytics."""
    return service.faculty(page, page_size, filters)


@router.get("/trends", response_model=TrendAnalyticsResponse)
def get_trends(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """8. Annual Funding and Proposal Trends."""
    return service.trends(filters)


@router.get("/concentration", response_model=ConcentrationAnalyticsResponse)
def get_concentration(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """9. Funding Concentration & PI vs Co-Investigator Analytics."""
    return service.concentration(filters)


@router.get("/export")
def export_csv(
    filters: dict = Depends(get_global_filters),
    _: dict = Depends(require_analytics_role),
    service: ProjectsFundingAnalyticsService = Depends(get_projects_funding_analytics_service),
):
    """10. CSV Export matching active filters."""
    rows = service.export_csv_rows(filters)
    output = io.StringIO()
    if rows:
        headers = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = 'attachment; filename="projects_funding_analytics_export.csv"'
    return response
