from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OverviewAnalyticsResponse(BaseModel):
    total_valid_journal_publications: int = 0
    publishing_faculty: int = 0
    total_active_faculty: int = 0
    publication_participation_rate: float = 0.0
    papers_per_active_faculty: float = 0.0
    papers_per_publishing_faculty: float = 0.0
    indexed_publications: int = 0
    indexed_publication_percentage: float = 0.0
    missing_indexing_count: int = 0
    missing_issn_count: int = 0
    unique_journal_count: int = 0
    duplicate_title_count: int = 0
    same_title_multiple_faculty_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DepartmentAnalyticsItem(BaseModel):
    school: Optional[str] = None
    department: Optional[str] = None
    active_faculty: int = 0
    total_papers: int = 0
    publishing_faculty: int = 0
    participation_rate: float = 0.0
    papers_per_active_faculty: float = 0.0
    papers_per_publishing_faculty: float = 0.0
    top_three_faculty_contribution_share: float = 0.0
    year_over_year_growth: float = 0.0
    quadrant_classification: str = "Low output, low participation"

    model_config = ConfigDict(from_attributes=True)


class PaginatedDepartmentAnalyticsResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[DepartmentAnalyticsItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FacultyJournalSummaryItem(BaseModel):
    faculty_email: Optional[str] = None
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    designation: Optional[str] = None
    total_publications: int = 0
    indexed_publications: int = 0
    academic_years_active: int = 0
    research_score: float = 0.0
    latest_validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class FacultyAnalyticsResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[FacultyJournalSummaryItem] = Field(default_factory=list)
    top_publishing_faculty: List[FacultyJournalSummaryItem] = Field(default_factory=list)
    faculty_with_zero_publications: List[FacultyJournalSummaryItem] = Field(default_factory=list)
    faculty_with_exactly_one_publication: List[FacultyJournalSummaryItem] = Field(default_factory=list)
    faculty_publishing_consecutive_years: List[FacultyJournalSummaryItem] = Field(default_factory=list)
    newly_active_publishing_faculty: List[FacultyJournalSummaryItem] = Field(default_factory=list)
    faculty_output_declined: List[FacultyJournalSummaryItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class IndexingDistributionItem(BaseModel):
    indexing: str
    count: int = 0
    percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class CommonJournalItem(BaseModel):
    journal: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class IndexingAverageScoreItem(BaseModel):
    indexing: str
    average_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class QualityIndexingAnalyticsResponse(BaseModel):
    indexing_category_distribution: List[IndexingDistributionItem] = Field(default_factory=list)
    missing_indexing: int = 0
    missing_issn: int = 0
    most_common_journals: List[CommonJournalItem] = Field(default_factory=list)
    unique_journal_count: int = 0
    duplicate_titles: int = 0
    same_title_submitted_by_multiple_faculty: int = 0
    average_score_by_indexing_type: List[IndexingAverageScoreItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class JournalRecordItem(BaseModel):
    id: Any
    faculty_email: Optional[str] = None
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    designation: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    issn: Optional[str] = None
    indexing: Optional[str] = None
    academic_year: Optional[Any] = None
    score: float = 0.0
    hod_score: float = 0.0
    director_score: float = 0.0
    dean_score: float = 0.0
    vc_score: float = 0.0
    final_validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class PaginatedJournalRecordResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 20
    items: List[JournalRecordItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AcademicYearCountItem(BaseModel):
    academic_year: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class JournalCountItem(BaseModel):
    journal: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ScoreSummaryItem(BaseModel):
    total_score: float = 0.0
    average_score: float = 0.0
    max_score: float = 0.0
    latest_validated_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class FacultyProfileItem(BaseModel):
    email: Optional[str] = None
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    designation: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class FacultyJournalDetailResponse(BaseModel):
    faculty_profile: FacultyProfileItem
    publication_records: List[JournalRecordItem] = Field(default_factory=list)
    publications_by_academic_year: List[AcademicYearCountItem] = Field(default_factory=list)
    journal_distribution: List[JournalCountItem] = Field(default_factory=list)
    indexing_distribution: List[IndexingDistributionItem] = Field(default_factory=list)
    score_summary: ScoreSummaryItem

    model_config = ConfigDict(from_attributes=True)
