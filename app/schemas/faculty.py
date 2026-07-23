from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.analytics import PublicationTrendItem, ScoreComparisonResponse


class FacultyAnalyticsItem(BaseModel):
    faculty_id: Any = Field(..., description="Unique faculty identifier")
    faculty_name: str = Field("Unknown faculty", description="Faculty full name")
    employee_id: Optional[str] = Field(None, description="Faculty employee ID")
    email: Optional[str] = Field(None, description="Faculty email address")
    school: Optional[str] = Field(None, description="School name")
    department: Optional[str] = Field(None, description="Department name")
    total_research_papers: int = Field(0, description="Total paper count")
    sci_papers: int = Field(0, description="SCI paper count")
    scopus_papers: int = Field(0, description="Scopus paper count")
    ugc_papers: int = Field(0, description="UGC paper count")
    other_indexed_papers: int = Field(0, description="Other indexed paper count")
    book_publications: int = Field(0, description="Book publications count")
    conference_publications: int = Field(0, description="Conference count")
    patents: int = Field(0, description="Patents count")
    research_projects: int = Field(0, description="Projects count")
    total_funding: float = Field(0.0, description="Total project funding")
    total_vc_score: float = Field(0.0, description="Total approved VC score")
    internal_projects: int = Field(0, description="Internal project count")
    external_projects: int = Field(0, description="External project count")


class PaginatedFacultyResponse(BaseModel):
    items: List[FacultyAnalyticsItem]
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    total: int = Field(0, ge=0)
    total_pages: int = Field(0, ge=0)


class FacultyDetailResponse(BaseModel):
    faculty: FacultyAnalyticsItem
    records: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    score_summary: ScoreComparisonResponse
    year_wise_activity_trend: List[PublicationTrendItem] = Field(default_factory=list)
