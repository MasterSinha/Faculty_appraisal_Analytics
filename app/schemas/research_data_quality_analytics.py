from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DataQualityAlertItem(BaseModel):
    id: str
    severity: str  # Critical, Warning, Informational
    alert_type: str
    category: str
    faculty_email: str
    faculty_name: str
    department: str
    school: str
    record_title: str
    academic_year: Optional[str] = "Unspecified"
    issue_description: str
    suggested_action: str
    record_table: str
    record_id: Any
    open_record_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SummaryDataQuality(BaseModel):
    total_alerts: int = 0
    critical_alerts: int = 0
    warning_alerts: int = 0
    informational_alerts: int = 0
    total_records_analyzed: int = 0
    records_with_alerts: int = 0
    completeness_percentage: float = 100.0

    model_config = ConfigDict(from_attributes=True)


class SeverityChartItem(BaseModel):
    severity: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CategoryChartItem(BaseModel):
    category: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DeptCompletenessChartItem(BaseModel):
    department: str
    completeness_percentage: float = 100.0

    model_config = ConfigDict(from_attributes=True)


class TopIssueTypeChartItem(BaseModel):
    alert_type: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TrendByYearChartItem(BaseModel):
    academic_year: str
    critical: int = 0
    warning: int = 0
    informational: int = 0

    model_config = ConfigDict(from_attributes=True)


class ChartsDataQuality(BaseModel):
    alerts_by_severity: List[SeverityChartItem] = Field(default_factory=list)
    alerts_by_category: List[CategoryChartItem] = Field(default_factory=list)
    completeness_by_department: List[DeptCompletenessChartItem] = Field(default_factory=list)
    top_issue_types: List[TopIssueTypeChartItem] = Field(default_factory=list)
    alert_trend_by_year: List[TrendByYearChartItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ResearchDataQualityAnalyticsResponse(BaseModel):
    items: List[DataQualityAlertItem] = Field(default_factory=list)
    alerts: List[DataQualityAlertItem] = Field(default_factory=list)
    summary: SummaryDataQuality
    charts: ChartsDataQuality
    completeness_percentage: float = 100.0
    review_supported: bool = False

    model_config = ConfigDict(from_attributes=True)
