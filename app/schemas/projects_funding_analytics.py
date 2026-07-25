from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OverviewProjectsFundingResponse(BaseModel):
    total_sanctioned_funding: float = 0.0
    total_proposed_funding: float = 0.0
    funded_project_count: int = 0
    proposal_count: int = 0
    average_project_amount: float = 0.0
    average_proposal_amount: float = 0.0
    external_funding_percentage: float = 0.0
    funding_per_active_faculty: float = 0.0
    funding_per_funded_faculty: float = 0.0
    faculty_receiving_project_funding: int = 0
    principal_investigator_count: int = 0
    ongoing_projects: int = 0
    completed_projects: int = 0
    proposal_to_project_indicator: float = 0.0
    proposal_to_project_indicator_note: str = "Approximate indicator because proposals and projects do not share a proposal identifier."

    model_config = ConfigDict(from_attributes=True)


class ProjectRecordItem(BaseModel):
    id: Any
    title: Optional[str] = None
    faculty_email: Optional[str] = None
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    agency: Optional[str] = None
    sanction_date: Optional[Any] = None
    amount: float = 0.0
    role: Optional[str] = None
    normalized_role: str = "Other"
    project_status: Optional[str] = None
    normalized_status: str = "Unknown"
    academic_year: Optional[Any] = None
    score: float = 0.0
    hod_score: float = 0.0
    director_score: float = 0.0
    dean_score: float = 0.0
    vc_score: float = 0.0
    final_validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PaginatedProjectRecordResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[ProjectRecordItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProposalRecordItem(BaseModel):
    id: Any
    title: Optional[str] = None
    faculty_email: Optional[str] = None
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    agency: Optional[str] = None
    duration: Optional[str] = None
    amount: float = 0.0
    academic_year: Optional[Any] = None
    score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PaginatedProposalRecordResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[ProposalRecordItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FundingAgencyItem(BaseModel):
    agency: str
    funded_project_count: int = 0
    proposal_count: int = 0
    total_sanctioned_amount: float = 0.0
    total_proposed_amount: float = 0.0
    average_project_amount: float = 0.0
    faculty_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DepartmentFundingItem(BaseModel):
    school: Optional[str] = None
    department: Optional[str] = None
    active_faculty: int = 0
    funded_project_count: int = 0
    proposal_count: int = 0
    total_sanctioned_funding: float = 0.0
    total_proposed_funding: float = 0.0
    external_funding: float = 0.0
    average_project_amount: float = 0.0
    faculty_receiving_funding: int = 0
    principal_investigator_count: int = 0
    ongoing_projects: int = 0
    completed_projects: int = 0

    model_config = ConfigDict(from_attributes=True)


class PaginatedDepartmentFundingResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[DepartmentFundingItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FacultyFundingItem(BaseModel):
    faculty_email: Optional[str] = None
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    designation: Optional[str] = None
    funded_project_count: int = 0
    proposal_count: int = 0
    total_sanctioned_funding: float = 0.0
    total_proposed_funding: float = 0.0
    principal_investigator_projects: int = 0
    co_investigator_projects: int = 0
    ongoing_projects: int = 0
    completed_projects: int = 0
    latest_validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PaginatedFacultyFundingResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[FacultyFundingItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FundingTrendItem(BaseModel):
    year: str
    sanctioned_amount: float = 0.0
    project_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProposalTrendItem(BaseModel):
    year: str
    proposed_amount: float = 0.0
    proposal_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class YoYFundingGrowthItem(BaseModel):
    year: str
    growth_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TrendAnalyticsResponse(BaseModel):
    funding_trend_by_sanction_date: List[FundingTrendItem] = Field(default_factory=list)
    proposal_trend_by_academic_year: List[ProposalTrendItem] = Field(default_factory=list)
    year_over_year_funding_growth: List[YoYFundingGrowthItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class HighestFundedFacultyItem(BaseModel):
    faculty_name: str
    department: str
    total_funding: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class RoleParticipationBreakdown(BaseModel):
    pi_count: int = 0
    co_pi_count: int = 0
    co_i_count: int = 0
    other_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ConcentrationAnalyticsResponse(BaseModel):
    top_five_faculty_funding_share: float = 0.0
    top_five_department_funding_share: float = 0.0
    faculty_with_highest_funding: List[HighestFundedFacultyItem] = Field(default_factory=list)
    departments_with_proposals_but_no_funded_projects: List[str] = Field(default_factory=list)
    faculty_with_proposals_but_no_funded_projects: List[str] = Field(default_factory=list)
    schools_with_no_external_projects: List[str] = Field(default_factory=list)
    pi_versus_coinvestigator_participation: RoleParticipationBreakdown
    ongoing_versus_completed_project_ratio: float = 0.0

    model_config = ConfigDict(from_attributes=True)
