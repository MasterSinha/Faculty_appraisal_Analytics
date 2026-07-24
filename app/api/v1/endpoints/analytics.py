from fastapi import APIRouter, Depends, Query
from app.api.deps import get_analytics_service, require_analytics_role
from app.schemas.analytics import (
    DataQualityAlertItem,
    DynamicInsightItem,
    FilterResponse,
    IndexingDistributionItem,
    OverviewResponse,
    PatentSummaryItem,
    ScoreComparisonResponse,
    TeachingResearchBalanceItem,
)
from app.services.research_analytics_service import ResearchAnalyticsService

router = APIRouter(tags=["Analytics Overview"])


@router.get("/schema")
def inspect_schema(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Inspect reflected database tables and key columns."""
    return service.inspect_schema()


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve high-level research KPIs and summary totals."""
    return service.overview()


@router.get("/publications/indexing")
def publications_by_indexing(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve paper distribution across indexing categories (SCI, Scopus, UGC, etc.)."""
    return {"data": service.indexing_distribution()}


@router.get("/publications/trend")
def publications_trend(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve year-over-year publication trend data."""
    return {"data": service.publication_trend()}


@router.get("/projects/summary")
def projects_summary(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve research project distribution by status, funding agency, and type."""
    return service.projects_summary()


@router.get("/scores/comparison", response_model=ScoreComparisonResponse)
def scores_comparison(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve multi-tier score breakdown (Self, Director, Dean, VC)."""
    return service.scores_comparison()


@router.get("/top-journals")
def top_journals(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve top published journals ordered by publication count."""
    return {"data": service.top_journals(limit)}


@router.get("/filters", response_model=FilterResponse)
def get_filters(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve available dynamic dropdown filter options."""
    return service.filters()


@router.get("/insights")
def get_insights(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Generate concise dynamic management insights."""
    return {"data": service.insights()}


@router.get("/patents/summary")
def get_patents_summary(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve patent and IPR distribution summary."""
    return {"data": service.patents_summary()}


@router.get("/teaching-balance")
def get_teaching_balance(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve Teaching versus Research balance quadrant mapping."""
    return {"data": service.teaching_balance()}


@router.get("/data-quality")
def get_data_quality(
    _: dict = Depends(require_analytics_role),
    service: ResearchAnalyticsService = Depends(get_analytics_service),
):
    """Retrieve data quality verification alerts."""
    return {"data": service.data_quality()}
