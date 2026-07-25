import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.repositories.school_performance_analytics_repository import SchoolPerformanceAnalyticsRepository

logger = logging.getLogger(__name__)


class SchoolPerformanceAnalyticsService:
    """Service layer for School Research Performance Analytics with robust error resilience."""

    def __init__(self, db: Session):
        self.repository = SchoolPerformanceAnalyticsRepository(db)

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(page, page_size, filters)
        except Exception as exc:
            logger.exception("Error during School Research Performance Analytics retrieval: %s", exc)
            return {
                "items": [],
                "summary": {
                    "total_schools": 0,
                    "active_faculty": 0,
                    "total_research_outputs": 0,
                    "total_funding": 0.0,
                    "overall_publication_participation": 0.0,
                    "overall_papers_per_faculty": 0.0,
                    "leading_school": None,
                },
                "charts": {
                    "output_by_school": [],
                    "funding_by_school": [],
                    "faculty_participation_by_school": [],
                    "papers_per_faculty_by_school": [],
                    "department_distribution_by_school": [],
                },
                "insights": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
            }
