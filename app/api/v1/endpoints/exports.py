from typing import Literal, Optional
from fastapi import APIRouter, Depends, Response

from app.api.deps import get_analytics_service, require_analytics_role
from app.services.research_analytics_service import ResearchAnalyticsService
from app.utils.export_utils import rows_to_csv, rows_to_xlsx

router = APIRouter(tags=["Export"])


@router.get("/export")
def export_research_analytics(
    format: Literal["csv", "xlsx"] = "csv",
    search: Optional[str] = None,
    school: Optional[str] = None,
    department: Optional[str] = None,
    indexing: Optional[str] = None,
    year: Optional[int] = None,
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Export filtered research analytics data as CSV or Excel spreadsheet."""
    filters = {
        "search": search,
        "school": school,
        "department": department,
        "indexing": indexing,
        "year": year,
    }
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
