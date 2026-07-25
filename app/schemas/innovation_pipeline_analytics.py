from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BaseInnovationRecord(BaseModel):
    id: Any
    faculty_email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    designation: Optional[str] = None
    academic_year: Optional[Any] = None
    title: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = 0.0
    score: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)


class PatentPipelineRecord(BaseInnovationRecord):
    patent_status: Optional[str] = None
    patent_date: Optional[Any] = None
    file_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IPRPipelineRecord(BaseInnovationRecord):
    ipr_status: Optional[str] = None
    ipr_date: Optional[Any] = None
    file_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectPipelineRecord(BaseInnovationRecord):
    project_status: Optional[str] = None
    sanction_date: Optional[Any] = None
    sanctioned_amount: Optional[float] = 0.0
    agency: Optional[str] = None
    role: Optional[str] = None
    external_project: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProductPipelineRecord(BaseInnovationRecord):
    product_title: Optional[str] = None
    development_date: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class ProposalPipelineRecord(BaseInnovationRecord):
    agency: Optional[str] = None
    duration: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AggregateFunnelStageItem(BaseModel):
    stage: str
    count: int = 0
    percentage_change_from_previous_stage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class DeptStageItem(BaseModel):
    department: str
    proposals: int = 0
    projects: int = 0
    patents_ipr: int = 0
    granted_patents: int = 0
    products: int = 0

    model_config = ConfigDict(from_attributes=True)


class SchoolStageItem(BaseModel):
    school: str
    proposals: int = 0
    projects: int = 0
    patents_ipr: int = 0
    products: int = 0

    model_config = ConfigDict(from_attributes=True)


class AcademicYearTrendItem(BaseModel):
    academic_year: str
    proposals: int = 0
    projects: int = 0
    patents_ipr: int = 0
    products: int = 0

    model_config = ConfigDict(from_attributes=True)


class FacultyDiversityItem(BaseModel):
    faculty_email: str
    full_name: str
    department: str
    categories_count: int = 0
    categories: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PipelineSummary(BaseModel):
    proposals_submitted: int = 0
    projects_sanctioned: int = 0
    patent_or_ipr_records: int = 0
    patents_granted: int = 0
    products_developed: int = 0
    innovation_active_faculty: int = 0
    limitation_note: str = "Pipeline stages represent aggregate institutional counts. Existing database records do not contain a shared innovation identifier, so individual proposals cannot be followed reliably through every stage."
    aggregate_funnel: List[AggregateFunnelStageItem] = Field(default_factory=list)
    pipeline_stages_by_department: List[DeptStageItem] = Field(default_factory=list)
    innovation_activity_by_school: List[SchoolStageItem] = Field(default_factory=list)
    academic_year_pipeline_trend: List[AcademicYearTrendItem] = Field(default_factory=list)
    faculty_innovation_diversity: List[FacultyDiversityItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class GapAnalytics(BaseModel):
    proposals_without_corresponding_aggregate_project_activity: int = 0
    departments_with_projects_but_no_patents: List[str] = Field(default_factory=list)
    faculty_with_patents_but_no_products: List[str] = Field(default_factory=list)
    departments_with_no_products_developed: List[str] = Field(default_factory=list)
    schools_with_no_external_projects: List[str] = Field(default_factory=list)
    faculty_active_in_three_or_more_innovation_categories: List[str] = Field(default_factory=list)
    departments_showing_strong_project_funding_but_weak_product_output: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DepartmentContributionItem(BaseModel):
    school: Optional[str] = None
    department: Optional[str] = None
    proposals: int = 0
    projects: int = 0
    patents_ipr: int = 0
    products: int = 0
    total_innovation_outputs: int = 0

    model_config = ConfigDict(from_attributes=True)


class SchoolContributionItem(BaseModel):
    school: str
    proposals: int = 0
    projects: int = 0
    patents_ipr: int = 0
    products: int = 0
    total_innovation_outputs: int = 0

    model_config = ConfigDict(from_attributes=True)


class InnovationPipelineAnalyticsResponse(BaseModel):
    research_proposals: List[ProposalPipelineRecord] = Field(default_factory=list)
    research_projects: List[ProjectPipelineRecord] = Field(default_factory=list)
    external_research_projects: List[ProjectPipelineRecord] = Field(default_factory=list)
    patents: List[PatentPipelineRecord] = Field(default_factory=list)
    ipr_records: List[IPRPipelineRecord] = Field(default_factory=list)
    products_developed: List[ProductPipelineRecord] = Field(default_factory=list)
    summary: PipelineSummary
    department_contribution: List[DepartmentContributionItem] = Field(default_factory=list)
    school_contribution: List[SchoolContributionItem] = Field(default_factory=list)
    academic_year_comparison: List[AcademicYearTrendItem] = Field(default_factory=list)
    faculty_innovation_diversity: List[FacultyDiversityItem] = Field(default_factory=list)
    gap_analytics: GapAnalytics

    model_config = ConfigDict(from_attributes=True)
