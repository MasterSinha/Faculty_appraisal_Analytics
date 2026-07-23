from typing import Any, List, Optional

from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    total_faculty: int = 0
    faculty_with_research: int = 0
    total_research_papers: int = 0
    total_projects: int = 0
    total_patents: int = 0
    total_books: int = 0
    total_conferences: int = 0
    total_funding: float = 0
    total_vc_score: float = 0


class IndexingDistributionItem(BaseModel):
    indexing: str
    total_papers: int = 0
    total_faculty: int = 0
    vc_score: float = 0


class FacultyAnalyticsItem(BaseModel):
    faculty_id: Any
    faculty_name: str = "Unknown faculty"
    employee_id: Optional[str] = None
    school: Optional[str] = None
    department: Optional[str] = None
    total_research_papers: int = 0
    sci_papers: int = 0
    scopus_papers: int = 0
    ugc_papers: int = 0
    book_publications: int = 0
    conference_publications: int = 0
    patents: int = 0
    research_projects: int = 0
    total_funding: float = 0
    total_vc_score: float = 0


class PaginatedFacultyResponse(BaseModel):
    items: List[FacultyAnalyticsItem]
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0


class ScoreComparisonResponse(BaseModel):
    self_score: float = 0
    director_score: float = 0
    dean_score: float = 0
    vc_score: float = 0
    reduced_by_director: int = 0
    reduced_by_dean: int = 0
    reduced_by_vc: int = 0
    unchanged_records: int = 0


class FilterResponse(BaseModel):
    schools: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    years: list[int] = Field(default_factory=list)
    indexing_categories: list[str] = Field(default_factory=list)
    project_statuses: list[str] = Field(default_factory=list)
    funding_agencies: list[str] = Field(default_factory=list)

