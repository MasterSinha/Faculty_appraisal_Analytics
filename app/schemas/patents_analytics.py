from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OverviewPatentsResponse(BaseModel):
    total_valid_patents: int = 0
    patent_filing_faculty: int = 0
    total_active_faculty: int = 0
    patents_granted: int = 0
    patents_pending: int = 0
    patent_grant_rate: float = 0.0
    total_ipr_records: int = 0
    patents_per_active_faculty: float = 0.0
    patent_participation_rate: float = 0.0
    average_patent_score: float = 0.0
    average_validated_patent_score: float = 0.0
    faculty_with_multiple_patents: int = 0
    faculty_with_journal_papers_but_no_patents: int = 0
    departments_with_no_patent_contribution: List[str] = Field(default_factory=list)
    departments_with_no_ipr_contribution: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class StatusDistributionItem(BaseModel):
    status: str
    count: int = 0
    percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SchoolGrantedShareItem(BaseModel):
    school: str
    granted_patents: int = 0
    percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PatentStatusAnalyticsResponse(BaseModel):
    patent_status_distribution: List[StatusDistributionItem] = Field(default_factory=list)
    ipr_status_distribution: List[StatusDistributionItem] = Field(default_factory=list)
    granted_patent_share_by_school: List[SchoolGrantedShareItem] = Field(default_factory=list)
    missing_status_count: int = 0
    duplicate_file_number_count: int = 0
    future_patent_date_count: int = 0
    missing_title_count: int = 0
    unmatched_faculty_email_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DepartmentPatentItem(BaseModel):
    school: Optional[str] = None
    department: Optional[str] = None
    active_faculty: int = 0
    total_valid_patents: int = 0
    patent_filing_faculty: int = 0
    patent_participation_rate: float = 0.0
    patents_granted: int = 0
    patents_pending: int = 0
    total_ipr_records: int = 0
    average_patent_score: float = 0.0
    average_validated_patent_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PaginatedDepartmentPatentResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[DepartmentPatentItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FacultyPatentItem(BaseModel):
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    school: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    total_valid_patents: int = 0
    patents_granted: int = 0
    patents_pending: int = 0
    total_ipr_records: int = 0
    average_score: float = 0.0
    latest_validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PaginatedFacultyPatentResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[FacultyPatentItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PatentRecordItem(BaseModel):
    id: Any
    faculty_email: Optional[str] = None
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    scope: Optional[str] = None
    normalized_scope: str = "Unknown"
    patent_date: Optional[Any] = None
    patent_status: Optional[str] = None
    normalized_status: str = "Unknown"
    file_no: Optional[str] = None
    academic_year: Optional[Any] = None
    score: float = 0.0
    hod_score: float = 0.0
    director_score: float = 0.0
    dean_score: float = 0.0
    vc_score: float = 0.0
    final_validated_score: float = 0.0
    flags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PaginatedPatentRecordResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[PatentRecordItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class IPRRecordItem(BaseModel):
    id: Any
    faculty_email: Optional[str] = None
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    scope: Optional[str] = None
    normalized_scope: str = "Unknown"
    ipr_date: Optional[Any] = None
    ipr_status: Optional[str] = None
    normalized_status: str = "Unknown"
    file_no: Optional[str] = None
    score: float = 0.0
    flags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PaginatedIPRRecordResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[IPRRecordItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PatentsByYearItem(BaseModel):
    year: str
    total_patents: int = 0
    patents_granted: int = 0

    model_config = ConfigDict(from_attributes=True)


class IPRByYearItem(BaseModel):
    year: str
    total_ipr: int = 0

    model_config = ConfigDict(from_attributes=True)


class YoYGrowthItem(BaseModel):
    year: str
    patent_growth_rate: float = 0.0
    ipr_growth_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TrendAnalyticsResponse(BaseModel):
    patents_by_year: List[PatentsByYearItem] = Field(default_factory=list)
    ipr_by_year: List[IPRByYearItem] = Field(default_factory=list)
    patent_ipr_year_over_year_growth: List[YoYGrowthItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
