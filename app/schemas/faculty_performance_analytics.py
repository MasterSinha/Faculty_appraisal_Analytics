from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FacultyRecordsDrawer(BaseModel):
    journals: List[Dict[str, Any]] = Field(default_factory=list)
    books: List[Dict[str, Any]] = Field(default_factory=list)
    patents: List[Dict[str, Any]] = Field(default_factory=list)
    ipr: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    external_projects: List[Dict[str, Any]] = Field(default_factory=list)
    proposals: List[Dict[str, Any]] = Field(default_factory=list)
    guidance: List[Dict[str, Any]] = Field(default_factory=list)
    conferences: List[Dict[str, Any]] = Field(default_factory=list)
    awards: List[Dict[str, Any]] = Field(default_factory=list)
    products: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FacultyPerformanceItem(BaseModel):
    faculty_email: str
    full_name: str
    employee_id: Optional[str] = "N/A"
    department: Optional[str] = "N/A"
    school: Optional[str] = "N/A"
    designation: Optional[str] = "N/A"
    journal_papers: int = 0
    books: int = 0
    patents: int = 0
    ipr_records: int = 0
    projects: int = 0
    proposals: int = 0
    funding: float = 0.0
    guidance: int = 0
    conferences: int = 0
    awards: int = 0
    products_developed: int = 0
    total_output: int = 0
    diversity_score: int = 0
    self_score: float = 0.0
    validated_research_score: float = 0.0
    current_year_output: int = 0
    previous_year_output: int = 0
    first_activity_year: Optional[int] = None
    consistency_years: int = 0
    missing_evidence_alerts: List[str] = Field(default_factory=list)
    segment: str = "Inactive Researchers"
    status_label: str = "No recorded research activity for the selected period."
    records: FacultyRecordsDrawer = Field(default_factory=FacultyRecordsDrawer)

    model_config = ConfigDict(from_attributes=True)


class SummaryPerformance(BaseModel):
    total_faculty: int = 0
    active_research_faculty: int = 0
    inactive_research_faculty: int = 0
    total_research_outputs: int = 0
    total_validated_score: float = 0.0
    average_diversity_score: float = 0.0
    total_funding_sanctioned: float = 0.0
    inactive_label: str = "No recorded research activity for the selected period."

    model_config = ConfigDict(from_attributes=True)


class SegmentsPerformance(BaseModel):
    research_leaders_count: int = 0
    active_contributors_count: int = 0
    emerging_researchers_count: int = 0
    specialists_count: int = 0
    declining_contributors_count: int = 0
    inactive_researchers_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TopFacultyOutputItem(BaseModel):
    faculty_name: str
    department: str
    total_output: int = 0

    model_config = ConfigDict(from_attributes=True)


class TopFacultyScoreItem(BaseModel):
    faculty_name: str
    department: str
    validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class DiversityDistributionItem(BaseModel):
    diversity_score: int
    faculty_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PerformanceTrendItem(BaseModel):
    academic_year: str
    total_output: int = 0
    validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class OutputVsParticipationScatterItem(BaseModel):
    faculty_email: str
    faculty_name: str
    department: str
    total_output: int = 0
    diversity_score: int = 0

    model_config = ConfigDict(from_attributes=True)


class SelfVsFinalScoreItem(BaseModel):
    faculty_name: str
    self_score: float = 0.0
    final_validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ChartsPerformance(BaseModel):
    top_faculty_by_output: List[TopFacultyOutputItem] = Field(default_factory=list)
    top_faculty_by_validated_score: List[TopFacultyScoreItem] = Field(default_factory=list)
    research_diversity_distribution: List[DiversityDistributionItem] = Field(default_factory=list)
    faculty_performance_trend: List[PerformanceTrendItem] = Field(default_factory=list)
    output_vs_participation_scatter: List[OutputVsParticipationScatterItem] = Field(default_factory=list)
    self_vs_final_score_comparison: List[SelfVsFinalScoreItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FacultyPerformanceAnalyticsResponse(BaseModel):
    items: List[FacultyPerformanceItem] = Field(default_factory=list)
    summary: SummaryPerformance
    segments: SegmentsPerformance
    charts: ChartsPerformance
    page: int = 1
    page_size: int = 500
    total: int = 0

    model_config = ConfigDict(from_attributes=True)
