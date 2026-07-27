from typing import Any, Optional
from pydantic import BaseModel, Field


class MetaResponse(BaseModel):
    cached: bool = False
    cache_ttl_seconds: int = 60
    generated_at: str = ""
    query_time_ms: float = 0.0
    filters_applied: dict[str, Any] = Field(default_factory=dict)


class KPISummaryItem(BaseModel):
    name: str
    value: Any
    unit: str = ""
    change: str = ""


class TrendSummaryItem(BaseModel):
    academic_year: str
    publications: int = 0
    funding: float = 0.0
    patents: int = 0
    books: int = 0


class SchoolSummaryItem(BaseModel):
    school: str
    total_faculty: int = 0
    active_faculty: int = 0
    publications: int = 0
    funding: float = 0.0
    patents: int = 0
    participation_rate: float = 0.0


class DepartmentSummaryItem(BaseModel):
    department: str
    school: str = ""
    total_faculty: int = 0
    active_faculty: int = 0
    publications: int = 0
    funding: float = 0.0
    patents: int = 0
    participation_rate: float = 0.0


class CategorySummaryItem(BaseModel):
    category: str
    count: int = 0
    total_score: float = 0.0
    total_amount: float = 0.0


class FundingSummaryItem(BaseModel):
    agency: str
    total_amount: float = 0.0
    project_count: int = 0


class PatentSummaryItem(BaseModel):
    status: str
    count: int = 0


class ResearchOverview(BaseModel):
    total_active_faculty: int = 0
    total_journal_publications: int = 0
    faculty_with_journal_publication: int = 0
    publication_participation_rate: float = 0.0
    average_publications_per_publishing_faculty: float = 0.0
    total_book_publications: int = 0
    faculty_with_book_publication: int = 0
    total_patents: int = 0
    patents_granted: int = 0
    total_research_projects: int = 0
    total_sanctioned_funding: float = 0.0
    external_funded_projects: int = 0
    external_funded_amount: float = 0.0
    total_research_proposals: int = 0
    total_proposal_amount: float = 0.0
    total_research_scholars_guided: int = 0
    total_conferences: int = 0
    total_awards: int = 0
    total_products_developed: int = 0
    funding_per_active_faculty: float = 0.0


class DashboardResponse(BaseModel):
    overview: dict[str, Any] = Field(default_factory=dict)
    kpis: list[dict[str, Any]] = Field(default_factory=list)
    trend: list[dict[str, Any]] = Field(default_factory=list)
    school_summary: list[dict[str, Any]] = Field(default_factory=list)
    department_summary: list[dict[str, Any]] = Field(default_factory=list)
    category_summary: list[dict[str, Any]] = Field(default_factory=list)
    funding_summary: list[dict[str, Any]] = Field(default_factory=list)
    patent_summary: list[dict[str, Any]] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    attention_alerts: list[dict[str, Any]] = Field(default_factory=list)
    filter_options: dict[str, Any] = Field(default_factory=dict)
    last_refreshed: str = ""
    meta: MetaResponse = Field(default_factory=MetaResponse)
    warnings: list[str] = Field(default_factory=list)


class PaginatedResponse(BaseModel):
    items: list[dict[str, Any]]
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0
    summary: Optional[dict[str, Any]] = None
    meta: Optional[MetaResponse] = None


class InsightResponse(BaseModel):
    insights: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
    database: str = "connected"
    cache: str = "enabled"
    dashboard_cache_keys: int = 0
    slowest_recent_endpoint: str = ""
    last_materialized_view_refresh: str = ""
