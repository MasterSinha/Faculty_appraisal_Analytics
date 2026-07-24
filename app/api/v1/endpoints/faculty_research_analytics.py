from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_faculty_research_analytics_service, require_analytics_role
from app.schemas.faculty_research_analytics import InsightResponse, PaginatedResponse, ResearchOverview
from app.services.faculty_research_analytics_service import FacultyResearchAnalyticsService
from app.utils.export_utils import rows_to_csv


router = APIRouter(prefix="/api/v1/analytics/research", tags=["Faculty Research Analytics"])


def query_filters(
    academic_year: Optional[str] = None,
    school: Optional[str] = None,
    department: Optional[str] = None,
    designation: Optional[str] = None,
    faculty_email: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    agency: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "academic_year": academic_year,
        "school": school,
        "department": department,
        "designation": designation,
        "faculty_email": faculty_email,
        "category": category,
        "status": status,
        "agency": agency,
        "date_from": date_from,
        "date_to": date_to,
    }


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
def publications(page: int = 1, page_size: int = 20, filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("journal_publications", filters, page, page_size)


@router.get("/books", response_model=PaginatedResponse)
def books(page: int = 1, page_size: int = 20, filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("book_publications", filters, page, page_size)


@router.get("/patents", response_model=PaginatedResponse)
def patents(page: int = 1, page_size: int = 20, filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("patents", filters, page, page_size)


@router.get("/projects", response_model=PaginatedResponse)
def projects(page: int = 1, page_size: int = 20, filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    return service.category_records("research_projects", filters, page, page_size)


@router.get("/funding")
def funding(filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
    overview_data = service.overview(filters)
    return {"total_sanctioned_funding": overview_data["total_sanctioned_funding"], "external_funded_amount": overview_data["external_funded_amount"], "funding_per_active_faculty": overview_data["funding_per_active_faculty"]}


@router.get("/guidance", response_model=PaginatedResponse)
def guidance(page: int = 1, page_size: int = 20, filters: dict[str, Any] = Depends(query_filters), _: dict = Depends(require_analytics_role), service: FacultyResearchAnalyticsService = Depends(get_faculty_research_analytics_service)):
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
