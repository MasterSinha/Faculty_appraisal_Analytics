from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StatusAnalyticsItem(BaseModel):
    status: str
    count: int = 0
    percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class DepartmentCompletionMetric(BaseModel):
    department: str
    school: str
    total_active_faculty: int = 0
    submitted_count: int = 0
    pending_count: int = 0
    completion_rate: float = 0.0
    research_active_not_submitted: int = 0
    records_without_documents: int = 0
    average_document_count_per_research_active_faculty: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class NotSubmittedItem(BaseModel):
    faculty_email: str
    full_name: str
    department: str
    school: str
    research_outputs: int = 0

    model_config = ConfigDict(from_attributes=True)


class ResearchActiveIncompleteItem(BaseModel):
    faculty_email: str
    full_name: str
    department: str
    school: str
    status: str
    missing_evidence_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SubmittedNoResearchItem(BaseModel):
    faculty_email: str
    full_name: str
    department: str
    school: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class RecordWithoutEvidenceItem(BaseModel):
    faculty_email: str
    full_name: str
    department: str
    record_type: str
    title: str
    evidence_mapping_status: str = "Unmapped"
    has_doc_key: bool = False
    has_section_mapping: bool = False

    model_config = ConfigDict(from_attributes=True)


class AwaitingReviewItem(BaseModel):
    faculty_email: str
    full_name: str
    department: str
    current_stage: str
    days_pending: int = 0

    model_config = ConfigDict(from_attributes=True)


class FollowUpTables(BaseModel):
    not_submitted: List[NotSubmittedItem] = Field(default_factory=list)
    research_active_incomplete: List[ResearchActiveIncompleteItem] = Field(default_factory=list)
    submitted_no_research: List[SubmittedNoResearchItem] = Field(default_factory=list)
    records_without_evidence: List[RecordWithoutEvidenceItem] = Field(default_factory=list)
    awaiting_review: List[AwaitingReviewItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SummaryAppraisalCompletion(BaseModel):
    active_faculty: int = 0
    submitted_appraisals: int = 0
    pending_appraisals: int = 0
    completion_percentage: float = 0.0
    research_active_faculty_not_submitted: int = 0
    research_records_missing_evidence: int = 0

    model_config = ConfigDict(from_attributes=True)


class SubmissionDeptChartItem(BaseModel):
    department: str
    submitted: int = 0
    pending: int = 0

    model_config = ConfigDict(from_attributes=True)


class SchoolCompletionChartItem(BaseModel):
    school: str
    completion_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class YearSubmissionTrendChartItem(BaseModel):
    academic_year: str
    submitted_count: int = 0
    total_faculty: int = 0

    model_config = ConfigDict(from_attributes=True)


class ActiveVsSubmittedChartItem(BaseModel):
    department: str
    research_active_faculty: int = 0
    submitted_faculty: int = 0

    model_config = ConfigDict(from_attributes=True)


class EvidenceCompletionChartItem(BaseModel):
    department: str
    records_with_evidence: int = 0
    records_missing_evidence: int = 0

    model_config = ConfigDict(from_attributes=True)


class ReviewStageDistChartItem(BaseModel):
    stage: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ChartsAppraisalCompletion(BaseModel):
    submission_status_by_department: List[SubmissionDeptChartItem] = Field(default_factory=list)
    completion_rate_by_school: List[SchoolCompletionChartItem] = Field(default_factory=list)
    submission_trend_by_academic_year: List[YearSubmissionTrendChartItem] = Field(default_factory=list)
    research_active_versus_submitted_faculty: List[ActiveVsSubmittedChartItem] = Field(default_factory=list)
    evidence_completion_by_department: List[EvidenceCompletionChartItem] = Field(default_factory=list)
    review_stage_distribution: List[ReviewStageDistChartItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AppraisalRecordItem(BaseModel):
    faculty_email: str
    full_name: str
    employee_id: Optional[str] = "N/A"
    department: Optional[str] = "N/A"
    school: Optional[str] = "N/A"
    designation: Optional[str] = "N/A"
    academic_year: Optional[str] = "All Years"
    status: str = "Pending Submission"
    submission_date: Optional[Any] = None
    document_count: int = 0
    research_records_count: int = 0
    missing_evidence_count: int = 0
    is_submitted: bool = False
    is_research_active: bool = False

    model_config = ConfigDict(from_attributes=True)


class AppraisalCompletionAnalyticsResponse(BaseModel):
    items: List[AppraisalRecordItem] = Field(default_factory=list)
    appraisals: List[Dict[str, Any]] = Field(default_factory=list)
    summary: SummaryAppraisalCompletion
    status_analytics: List[StatusAnalyticsItem] = Field(default_factory=list)
    department_metrics: List[DepartmentCompletionMetric] = Field(default_factory=list)
    tables: FollowUpTables
    charts: ChartsAppraisalCompletion

    model_config = ConfigDict(from_attributes=True)
