import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.repositories.teaching_research_balance_analytics_repository import TeachingResearchBalanceAnalyticsRepository

logger = logging.getLogger(__name__)


class TeachingResearchBalanceAnalyticsService:
    """Service layer for Teaching vs Research Analytics with robust error resilience."""

    def __init__(self, db: Session):
        self.repository = TeachingResearchBalanceAnalyticsRepository(db)

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(page, page_size, filters)
        except Exception as exc:
            logger.exception("Error during Teaching vs Research Analytics retrieval: %s", exc)
            return {
                "items": [],
                "summary": {
                    "balanced_high_performers": 0,
                    "teaching_focused_faculty": 0,
                    "research_focused_faculty": 0,
                    "development_opportunity_group": 0,
                    "average_teaching_score": 0.0,
                    "average_research_score": 0.0,
                    "disclaimer": "This dashboard shows associations within recorded appraisal data. It does not prove that one activity caused another.",
                },
                "quadrants": {
                    "balanced_leaders_count": 0,
                    "teaching_focused_count": 0,
                    "research_focused_count": 0,
                    "development_opportunity_count": 0,
                },
                "department_balance": [],
                "teaching_components": {
                    "teaching_process_avg_pct": 0.0,
                    "student_feedback_avg_pct": 0.0,
                    "innovative_teaching_avg_pct": 0.0,
                    "ict_usage_avg_pct": 0.0,
                    "course_files_avg_pct": 0.0,
                    "self_development_avg_pct": 0.0,
                },
                "research_components": {
                    "publications_avg_pct": 0.0,
                    "projects_avg_pct": 0.0,
                    "patents_avg_pct": 0.0,
                },
                "trends": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
            }
