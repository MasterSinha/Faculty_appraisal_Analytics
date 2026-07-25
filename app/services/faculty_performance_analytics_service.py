import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.repositories.faculty_performance_analytics_repository import FacultyPerformanceAnalyticsRepository

logger = logging.getLogger(__name__)


class FacultyPerformanceAnalyticsService:
    """Service layer for Faculty Research Performance Analytics with robust error resilience."""

    def __init__(self, db: Session):
        self.repository = FacultyPerformanceAnalyticsRepository(db)

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(page, page_size, filters)
        except Exception as exc:
            logger.exception("Error during Faculty Research Performance Analytics retrieval: %s", exc)
            return {
                "items": [],
                "summary": {
                    "active_faculty": 0,
                    "total_research_outputs": 0,
                    "publishing_faculty": 0,
                    "publication_participation_rate": 0.0,
                    "papers_per_faculty": 0.0,
                    "high_performers_count": 0,
                    "moderate_performers_count": 0,
                    "low_performers_count": 0,
                    "inactive_researchers_count": 0,
                    "average_self_score": 0.0,
                    "average_validated_score": 0.0,
                    "score_variance_average": 0.0,
                },
                "segments": {
                    "high_performers": [],
                    "moderate_performers": [],
                    "low_performers": [],
                    "inactive_researchers": [],
                },
                "charts": {
                    "performance_segmentation": [],
                    "department_output_comparison": [],
                    "score_distribution": [],
                    "output_trend_by_year": [],
                    "diversity_score_distribution": [],
                },
                "page": page,
                "page_size": page_size,
                "total": 0,
            }
