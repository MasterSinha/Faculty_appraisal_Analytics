from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_research_data_quality_analytics_service, require_analytics_role
from app.schemas.research_data_quality_analytics import ResearchDataQualityAnalyticsResponse
from app.services.research_data_quality_analytics_service import ResearchDataQualityAnalyticsService

router = APIRouter(prefix="/api/v1/analytics/research", tags=["Research Data Quality Analytics Module"])


@router.get("/data-quality", response_model=ResearchDataQualityAnalyticsResponse)
def get_research_data_quality_analytics(
    severity: Optional[str] = Query(None, description="Severity filter: Critical, Warning, Informational"),
    category: Optional[str] = Query(None, description="Category filter (e.g. Journals, Books, Patents, Projects)"),
    department: Optional[str] = Query(None, description="Department filter"),
    academic_year: Optional[str] = Query(None, description="Academic year filter (e.g. 2023-24)"),
    school: Optional[str] = Query(None, description="School filter"),
    faculty: Optional[str] = Query(None, description="Faculty email or name filter"),
    _: dict = Depends(require_analytics_role),
    service: ResearchDataQualityAnalyticsService = Depends(get_research_data_quality_analytics_service),
):
    """Retrieve Research Data Quality Analytics including 23 automated data quality checks, alert items, KPI summary, and charts."""
    filters = {
        "severity": severity,
        "category": category,
        "department": department,
        "academic_year": academic_year,
        "school": school,
        "faculty": faculty,
    }
    return service.get_analytics(filters)
