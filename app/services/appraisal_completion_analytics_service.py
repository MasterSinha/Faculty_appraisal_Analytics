import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.repositories.appraisal_completion_analytics_repository import AppraisalCompletionAnalyticsRepository

logger = logging.getLogger(__name__)


class AppraisalCompletionAnalyticsService:
    """Service layer for Appraisal Completion Analytics with robust error resilience."""

    def __init__(self, db: Session):
        self.repository = AppraisalCompletionAnalyticsRepository(db)

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(filters)
        except Exception as exc:
            logger.exception("Error during Appraisal Completion Analytics retrieval: %s", exc)
            return {
                "items": [],
                "appraisals": [],
                "summary": {
                    "active_faculty": 0,
                    "submitted_appraisals": 0,
                    "pending_appraisals": 0,
                    "completion_percentage": 0.0,
                    "research_active_faculty_not_submitted": 0,
                    "research_records_missing_evidence": 0,
                },
                "status_analytics": [],
                "department_metrics": [],
                "tables": {
                    "not_submitted": [],
                    "research_active_incomplete": [],
                    "submitted_no_research": [],
                    "records_without_evidence": [],
                    "awaiting_review": [],
                },
                "charts": {
                    "submission_status_by_department": [],
                    "completion_rate_by_school": [],
                    "submission_trend_by_academic_year": [],
                    "research_active_versus_submitted_faculty": [],
                    "evidence_completion_by_department": [],
                    "review_stage_distribution": [],
                },
            }
