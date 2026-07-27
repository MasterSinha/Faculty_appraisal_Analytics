from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthComponents(BaseModel):
    publication_participation: float = 0.0
    output_per_faculty: float = 0.0
    funding_performance: float = 0.0
    patent_ipr_performance: float = 0.0
    research_guidance: float = 0.0
    yoy_growth: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TopFacultyPerformanceItem(BaseModel):
    faculty_name: str
    faculty_email: str
    total_output: int = 0
    validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class FundingAgencyItem(BaseModel):
    agency: str
    amount: float = 0.0
    project_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PatentStatusBreakdown(BaseModel):
    granted: int = 0
    filed: int = 0
    pending: int = 0
    other: int = 0

    model_config = ConfigDict(from_attributes=True)


class DepartmentDetailDrawer(BaseModel):
    faculty_distribution: List[Dict[str, Any]] = Field(default_factory=list)
    category_contributions: List[Dict[str, Any]] = Field(default_factory=list)
    top_faculty: List[TopFacultyPerformanceItem] = Field(default_factory=list)
    research_concentration: float = 0.0
    funding_agencies: List[FundingAgencyItem] = Field(default_factory=list)
    patent_status: PatentStatusBreakdown = Field(default_factory=PatentStatusBreakdown)
    guidance_participation: Dict[str, Any] = Field(default_factory=dict)
    gaps: List[str] = Field(default_factory=list)
    data_quality_issues: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DepartmentPerformanceItem(BaseModel):
    school: str
    department: str
    active_faculty: int = 0
    total_research_output: int = 0
    publishing_faculty: int = 0
    publication_participation_rate: float = 0.0
    papers_per_active_faculty: float = 0.0
    journal_papers: int = 0
    books: int = 0
    patents: int = 0
    ipr_records: int = 0
    projects: int = 0
    funding: float = 0.0
    research_guidance: int = 0
    diversity_score: int = 0
    year_over_year_growth: float = 0.0
    research_health_score: float = 0.0
    health_category: str = "Needs Attention"
    health_components: HealthComponents = Field(default_factory=HealthComponents)
    inactive_faculty_percentage: float = 0.0
    data_completeness: float = 0.0
    funding_concentration: float = 0.0
    research_concentration: float = 0.0
    top_faculty: List[TopFacultyPerformanceItem] = Field(default_factory=list)
    funding_agencies: List[FundingAgencyItem] = Field(default_factory=list)
    patent_status: PatentStatusBreakdown = Field(default_factory=PatentStatusBreakdown)
    gaps: List[str] = Field(default_factory=list)
    data_quality_issues: List[str] = Field(default_factory=list)
    detail_drawer: Optional[DepartmentDetailDrawer] = None

    model_config = ConfigDict(from_attributes=True)


class SummaryDepartmentPerformance(BaseModel):
    total_departments: int = 0
    total_active_faculty: int = 0
    total_research_outputs: int = 0
    average_participation_rate: float = 0.0
    average_health_score: float = 0.0
    total_funding_sanctioned: float = 0.0
    excellent_health_departments: int = 0
    needs_attention_departments: int = 0

    model_config = ConfigDict(from_attributes=True)


class DeptOutputRankingItem(BaseModel):
    department: str
    school: str
    total_output: int = 0

    model_config = ConfigDict(from_attributes=True)


class DeptParticipationItem(BaseModel):
    department: str
    participation_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class DeptFundingItem(BaseModel):
    department: str
    funding: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class DeptPatentIPRItem(BaseModel):
    department: str
    patents: int = 0
    ipr: int = 0

    model_config = ConfigDict(from_attributes=True)


class DeptHeatmapItem(BaseModel):
    department: str
    journals: int = 0
    books: int = 0
    patents: int = 0
    projects: int = 0
    conferences: int = 0

    model_config = ConfigDict(from_attributes=True)


class DeptYoYItem(BaseModel):
    department: str
    yoy_growth: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class DeptHealthBreakdownItem(BaseModel):
    department: str
    health_score: float = 0.0
    category: str
    components: HealthComponents

    model_config = ConfigDict(from_attributes=True)


class ChartsDepartmentPerformance(BaseModel):
    department_output_ranking: List[DeptOutputRankingItem] = Field(default_factory=list)
    participation_rate_by_department: List[DeptParticipationItem] = Field(default_factory=list)
    funding_by_department: List[DeptFundingItem] = Field(default_factory=list)
    patent_ipr_activity: List[DeptPatentIPRItem] = Field(default_factory=list)
    department_category_heatmap: List[DeptHeatmapItem] = Field(default_factory=list)
    year_over_year_growth: List[DeptYoYItem] = Field(default_factory=list)
    research_health_score_breakdown: List[DeptHealthBreakdownItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DepartmentPerformanceAnalyticsResponse(BaseModel):
    items: List[DepartmentPerformanceItem] = Field(default_factory=list)
    summary: SummaryDepartmentPerformance
    charts: ChartsDepartmentPerformance
    page: int = 1
    page_size: int = 500
    total: int = 0
    meta: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
