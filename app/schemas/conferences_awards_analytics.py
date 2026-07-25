from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConferenceRecordItem(BaseModel):
    id: Any
    faculty_email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    organisation: Optional[str] = None
    organization: Optional[str] = None
    level: Optional[str] = None
    academic_year: Optional[Any] = None
    score: float = 0.0
    hod_score: float = 0.0
    director_score: float = 0.0
    dean_score: float = 0.0
    vc_score: float = 0.0
    journal_publications: int = 0

    model_config = ConfigDict(from_attributes=True)


class AwardRecordItem(BaseModel):
    id: Any
    faculty_email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    title: Optional[str] = None
    award_date: Optional[Any] = None
    agency: Optional[str] = None
    level: Optional[str] = None
    academic_year: Optional[Any] = None
    score: float = 0.0
    hod_score: float = 0.0
    director_score: float = 0.0
    dean_score: float = 0.0
    vc_score: float = 0.0
    journal_publications: int = 0

    model_config = ConfigDict(from_attributes=True)


class GroupCountItem(BaseModel):
    category: str = ""
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DepartmentGroupCountItem(BaseModel):
    department: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SchoolGroupCountItem(BaseModel):
    school: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class YearGroupCountItem(BaseModel):
    academic_year: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TypeGroupCountItem(BaseModel):
    type: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class LevelGroupCountItem(BaseModel):
    level: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AgencyGroupCountItem(BaseModel):
    agency: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class OrganisationGroupCountItem(BaseModel):
    organisation: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TopAwardFacultyItem(BaseModel):
    faculty_name: str
    department: str
    award_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ParticipationBreakdown(BaseModel):
    national: int = 0
    international: int = 0
    other: int = 0

    model_config = ConfigDict(from_attributes=True)


class SummaryAnalytics(BaseModel):
    total_conferences: int = 0
    conference_participating_faculty: int = 0
    conference_participation_rate: float = 0.0
    total_awards: int = 0
    award_receiving_faculty: int = 0
    international_level_activities: int = 0
    conferences_by_department: List[DepartmentGroupCountItem] = Field(default_factory=list)
    conferences_by_school: List[SchoolGroupCountItem] = Field(default_factory=list)
    conferences_by_academic_year: List[YearGroupCountItem] = Field(default_factory=list)
    conferences_by_type: List[TypeGroupCountItem] = Field(default_factory=list)
    conferences_by_level: List[LevelGroupCountItem] = Field(default_factory=list)
    national_versus_international_participation: ParticipationBreakdown = Field(default_factory=ParticipationBreakdown)
    top_organising_institutions: List[OrganisationGroupCountItem] = Field(default_factory=list)
    awards_by_department: List[DepartmentGroupCountItem] = Field(default_factory=list)
    awards_by_school: List[SchoolGroupCountItem] = Field(default_factory=list)
    awards_by_level: List[LevelGroupCountItem] = Field(default_factory=list)
    awards_by_agency: List[AgencyGroupCountItem] = Field(default_factory=list)
    awards_by_academic_year: List[YearGroupCountItem] = Field(default_factory=list)
    top_award_receiving_faculty: List[TopAwardFacultyItem] = Field(default_factory=list)
    average_conference_score: float = 0.0
    average_award_score: float = 0.0
    faculty_with_multiple_conference_activities: int = 0
    departments_with_high_conference_participation_but_low_publications: List[str] = Field(default_factory=list)
    faculty_receiving_awards_after_recorded_research_contributions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DepartmentComparisonItem(BaseModel):
    school: Optional[str] = None
    department: Optional[str] = None
    active_faculty: int = 0
    total_conferences: int = 0
    conference_participating_faculty: int = 0
    total_awards: int = 0
    award_receiving_faculty: int = 0
    total_journal_publications: int = 0
    average_conference_score: float = 0.0
    average_award_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class FacultyDetailItem(BaseModel):
    faculty_email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    school: Optional[str] = None
    designation: Optional[str] = None
    conference_count: int = 0
    award_count: int = 0
    journal_publication_count: int = 0
    average_conference_score: float = 0.0
    average_award_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ConferencesAwardsAnalyticsResponse(BaseModel):
    conferences: List[ConferenceRecordItem] = Field(default_factory=list)
    awards: List[AwardRecordItem] = Field(default_factory=list)
    summary: SummaryAnalytics
    department_comparison: List[DepartmentComparisonItem] = Field(default_factory=list)
    faculty_details: List[FacultyDetailItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
