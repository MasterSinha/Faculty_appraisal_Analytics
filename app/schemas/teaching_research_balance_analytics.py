from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FacultyBalanceItem(BaseModel):
    faculty_email: str
    full_name: str
    employee_id: Optional[str] = "N/A"
    department: Optional[str] = "N/A"
    school: Optional[str] = "N/A"
    designation: Optional[str] = "N/A"
    academic_year: Optional[str] = "All Years"

    teaching_score: float = 0.0
    teaching_max_marks: float = 100.0
    teaching_score_percentage: float = 0.0

    research_score: float = 0.0
    research_max_marks: float = 100.0
    research_score_percentage: float = 0.0

    student_feedback_score: float = 0.0
    student_feedback_max_marks: float = 25.0
    student_feedback_score_percentage: float = 0.0

    innovative_teaching_score: float = 0.0
    innovative_teaching_max_marks: float = 15.0
    innovative_teaching_score_percentage: float = 0.0

    ict_usage_score: float = 0.0
    ict_usage_max_marks: float = 15.0
    ict_usage_score_percentage: float = 0.0

    teaching_process_score: float = 0.0
    teaching_process_max_marks: float = 25.0
    teaching_process_score_percentage: float = 0.0

    course_files_score: float = 0.0
    course_files_max_marks: float = 10.0
    course_files_score_percentage: float = 0.0

    self_development_score: float = 0.0
    self_development_max_marks: float = 10.0
    self_development_score_percentage: float = 0.0

    publications_score: float = 0.0
    publications_max_marks: float = 50.0
    publications_score_percentage: float = 0.0

    projects_score: float = 0.0
    projects_max_marks: float = 30.0
    projects_score_percentage: float = 0.0

    patents_score: float = 0.0
    patents_max_marks: float = 20.0
    patents_score_percentage: float = 0.0

    quadrant: str = "Development Opportunity"

    model_config = ConfigDict(from_attributes=True)


class SummaryTeachingResearch(BaseModel):
    balanced_high_performers: int = 0
    teaching_focused_faculty: int = 0
    research_focused_faculty: int = 0
    development_opportunity_group: int = 0
    average_teaching_score: float = 0.0
    average_research_score: float = 0.0
    disclaimer: str = "This dashboard shows associations within recorded appraisal data. It does not prove that one activity caused another."

    model_config = ConfigDict(from_attributes=True)


class QuadrantsSummary(BaseModel):
    balanced_leaders_count: int = 0
    teaching_focused_count: int = 0
    research_focused_count: int = 0
    development_opportunity_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DeptBalanceItem(BaseModel):
    school: str
    department: str
    active_faculty: int = 0
    balanced_leaders: int = 0
    teaching_focused: int = 0
    research_focused: int = 0
    development_opportunity: int = 0
    avg_teaching_pct: float = 0.0
    avg_research_pct: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ComponentDistributionItem(BaseModel):
    component: str
    avg_score_pct: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TeachingComponentsSummary(BaseModel):
    teaching_process_avg_pct: float = 0.0
    student_feedback_avg_pct: float = 0.0
    innovative_teaching_avg_pct: float = 0.0
    ict_usage_avg_pct: float = 0.0
    course_files_avg_pct: float = 0.0
    self_development_avg_pct: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ResearchComponentsSummary(BaseModel):
    publications_avg_pct: float = 0.0
    projects_avg_pct: float = 0.0
    patents_avg_pct: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class BalanceTrendItem(BaseModel):
    academic_year: str
    avg_teaching_pct: float = 0.0
    avg_research_pct: float = 0.0
    balanced_leaders_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class QuadrantDistributionItem(BaseModel):
    quadrant: str
    count: int = 0
    percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TeachingResearchBalanceAnalyticsResponse(BaseModel):
    items: List[FacultyBalanceItem] = Field(default_factory=list)
    summary: SummaryTeachingResearch
    quadrants: QuadrantsSummary
    department_balance: List[DeptBalanceItem] = Field(default_factory=list)
    teaching_components: TeachingComponentsSummary
    research_components: ResearchComponentsSummary
    trends: List[BalanceTrendItem] = Field(default_factory=list)
    page: int = 1
    page_size: int = 500
    total: int = 0

    model_config = ConfigDict(from_attributes=True)
