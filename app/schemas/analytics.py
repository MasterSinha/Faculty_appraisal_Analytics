from typing import List
from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    total_faculty: int = Field(0, description="Total faculty count")
    faculty_with_research: int = Field(0, description="Count of faculty with published research")
    total_research_papers: int = Field(0, description="Total published papers")
    total_projects: int = Field(0, description="Total research projects and proposals")
    total_patents: int = Field(0, description="Total registered patents")
    total_books: int = Field(0, description="Total book publications")
    total_conferences: int = Field(0, description="Total conference publications")
    total_funding: float = Field(0.0, description="Total funding amount in local currency")
    total_vc_score: float = Field(0.0, description="Aggregate VC approved score")


class IndexingDistributionItem(BaseModel):
    indexing: str = Field(..., description="Normalized indexing category (e.g., SCI, Scopus, UGC)")
    total_papers: int = Field(0, description="Paper count for indexing category")
    total_faculty: int = Field(0, description="Distinct faculty count")
    vc_score: float = Field(0.0, description="Aggregate VC score for category")


class ScoreComparisonResponse(BaseModel):
    self_score: float = Field(0.0, description="Total self-appraisal score")
    director_score: float = Field(0.0, description="Total director-approved score")
    dean_score: float = Field(0.0, description="Total dean-approved score")
    vc_score: float = Field(0.0, description="Total final VC score")
    reduced_by_director: int = Field(0, description="Records with score reduced by director")
    reduced_by_dean: int = Field(0, description="Records with score reduced by dean")
    reduced_by_vc: int = Field(0, description="Records with score reduced by VC")
    unchanged_records: int = Field(0, description="Records with unchanged scores across evaluators")


class FilterResponse(BaseModel):
    schools: List[str] = Field(default_factory=list, description="Available school filter options")
    departments: List[str] = Field(default_factory=list, description="Available department filter options")
    years: List[int] = Field(default_factory=list, description="Available publication year options")
    indexing_categories: List[str] = Field(default_factory=list, description="Available indexing filter options")
    project_statuses: List[str] = Field(default_factory=list, description="Available project status options")
    funding_agencies: List[str] = Field(default_factory=list, description="Available funding agency options")


class ProjectSummaryItem(BaseModel):
    group: str = Field(..., description="Grouping taxonomy (status, funding_agency, project_type)")
    name: str = Field(..., description="Group value name")
    total: int = Field(0, description="Count of projects in group")
    amount: float = Field(0.0, description="Total sanctioned amount in group")


class PublicationTrendItem(BaseModel):
    year: int = Field(..., description="Publication year")
    total_papers: int = Field(0, description="Paper count for year")


class JournalItem(BaseModel):
    journal: str = Field(..., description="Journal name")
    total: int = Field(0, description="Publication count")
