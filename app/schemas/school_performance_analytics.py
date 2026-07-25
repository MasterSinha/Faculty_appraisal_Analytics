from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SchoolDeptComparisonItem(BaseModel):
    department: str
    active_faculty: int = 0
    total_output: int = 0
    funding: float = 0.0
    participation_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SchoolFundingAgencyItem(BaseModel):
    agency: str
    amount: float = 0.0
    project_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SchoolDetailDrawer(BaseModel):
    department_comparison: List[SchoolDeptComparisonItem] = Field(default_factory=list)
    faculty_participation: Dict[str, Any] = Field(default_factory=dict)
    research_category_profile: List[Dict[str, Any]] = Field(default_factory=list)
    funding_agency_profile: List[SchoolFundingAgencyItem] = Field(default_factory=list)
    patents: Dict[str, Any] = Field(default_factory=dict)
    guidance: Dict[str, Any] = Field(default_factory=dict)
    growth: Dict[str, Any] = Field(default_factory=dict)
    data_quality_issues: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SchoolPerformanceItem(BaseModel):
    school: str
    active_faculty: int = 0
    departments: int = 0
    total_output: int = 0
    publication_participation: float = 0.0
    papers_per_faculty: float = 0.0
    journal_papers: int = 0
    books: int = 0
    patents: int = 0
    ipr_records: int = 0
    research_projects: int = 0
    external_projects: int = 0
    total_funding: float = 0.0
    students_guided: int = 0
    awards: int = 0
    products: int = 0
    diversity_score: int = 0
    year_over_year_growth: float = 0.0
    funding_agencies: List[SchoolFundingAgencyItem] = Field(default_factory=list)
    dependent_researcher_share: float = 0.0
    data_quality_issues: List[str] = Field(default_factory=list)
    department_comparison: List[SchoolDeptComparisonItem] = Field(default_factory=list)
    detail_drawer: Optional[SchoolDetailDrawer] = None

    model_config = ConfigDict(from_attributes=True)


class SummarySchoolPerformance(BaseModel):
    total_schools: int = 0
    highest_research_output_school: str = "N/A"
    highest_funded_school: str = "N/A"
    highest_participation_school: str = "N/A"
    highest_patent_producing_school: str = "N/A"
    schools_with_no_external_project: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SchoolCatComparisonItem(BaseModel):
    school: str
    journals: int = 0
    books: int = 0
    patents: int = 0
    projects: int = 0
    conferences: int = 0

    model_config = ConfigDict(from_attributes=True)


class SchoolParticipationItem(BaseModel):
    school: str
    publication_participation: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SchoolFundingItem(BaseModel):
    school: str
    total_funding: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SchoolPatentIPRItem(BaseModel):
    school: str
    patents: int = 0
    ipr: int = 0

    model_config = ConfigDict(from_attributes=True)


class SchoolTrendItem(BaseModel):
    academic_year: str
    total_output: int = 0
    total_funding: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SchoolDiversityItem(BaseModel):
    school: str
    diversity_score: int = 0

    model_config = ConfigDict(from_attributes=True)


class SchoolContributionPctItem(BaseModel):
    school: str
    percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ChartsSchoolPerformance(BaseModel):
    research_category_comparison_by_school: List[SchoolCatComparisonItem] = Field(default_factory=list)
    publication_participation_by_school: List[SchoolParticipationItem] = Field(default_factory=list)
    funding_by_school: List[SchoolFundingItem] = Field(default_factory=list)
    patent_ipr_contribution_by_school: List[SchoolPatentIPRItem] = Field(default_factory=list)
    academic_year_trend: List[SchoolTrendItem] = Field(default_factory=list)
    school_research_diversity: List[SchoolDiversityItem] = Field(default_factory=list)
    school_contribution_percentage_to_university_output: List[SchoolContributionPctItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SchoolPerformanceAnalyticsResponse(BaseModel):
    items: List[SchoolPerformanceItem] = Field(default_factory=list)
    summary: SummarySchoolPerformance
    charts: ChartsSchoolPerformance
    insights: List[str] = Field(default_factory=list)
    page: int = 1
    page_size: int = 500
    total: int = 0

    model_config = ConfigDict(from_attributes=True)
