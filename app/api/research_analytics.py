from typing import Literal, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import get_db
from app.schemas.research_analytics import (
    FilterResponse,
    OverviewResponse,
    PaginatedFacultyResponse,
    ScoreComparisonResponse,
)
from app.services.research_analytics_service import ResearchAnalyticsService
from app.utils.export_utils import rows_to_csv, rows_to_xlsx


router = APIRouter(prefix="/api/v1/research-analytics", tags=["Research Analytics"])
security = HTTPBearer(auto_error=True)
ALLOWED_ROLES = {"admin", "director", "dean", "registrar", "vc"}


def require_analytics_role(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.") from exc

    role = str(payload.get("role") or payload.get("user_role") or "").lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    return payload


def get_service(db: Session = Depends(get_db)) -> ResearchAnalyticsService:
    return ResearchAnalyticsService(db)


@router.get("/schema")
def inspect_schema(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return service.inspect_schema()


@router.get("/overview", response_model=OverviewResponse)
def overview(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return service.overview()


@router.get("/publications/indexing")
def publications_by_indexing(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return {"data": service.indexing_distribution()}


@router.get("/faculty", response_model=PaginatedFacultyResponse)
def faculty_summary(
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
    service: ResearchAnalyticsService = Depends(get_service),
):
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
def faculty_detail(
    faculty_id: str,
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return service.faculty_detail(faculty_id)


@router.get("/publications/trend")
def publications_trend(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return {"data": service.publication_trend()}


@router.get("/projects/summary")
def projects_summary(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return service.projects_summary()


@router.get("/scores/comparison", response_model=ScoreComparisonResponse)
def scores_comparison(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return service.scores_comparison()


@router.get("/top-faculty")
def top_faculty(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return {"data": service.top_faculty(limit)}


@router.get("/top-journals")
def top_journals(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return {"data": service.top_journals(limit)}


@router.get("/filters", response_model=FilterResponse)
def filters(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    return service.filters()


@router.get("/export")
def export(
    format: Literal["csv", "xlsx"] = "csv",
    search: Optional[str] = None,
    school: Optional[str] = None,
    department: Optional[str] = None,
    indexing: Optional[str] = None,
    year: Optional[int] = None,
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_service),
):
    filters = {"search": search, "school": school, "department": department, "indexing": indexing, "year": year}
    rows = service.export_rows(filters)
    if format == "xlsx":
        return Response(
            content=rows_to_xlsx(rows),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=research-analytics.xlsx"},
        )
    return Response(
        content=rows_to_csv(rows),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=research-analytics.csv"},
    )

