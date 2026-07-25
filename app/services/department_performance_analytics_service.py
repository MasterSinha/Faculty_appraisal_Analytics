import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.repositories.department_performance_analytics_repository import DepartmentPerformanceAnalyticsRepository

logger = logging.getLogger(__name__)


class DepartmentPerformanceAnalyticsService:
    """Service layer for Department Research Performance Analytics with robust error resilience."""

    def __init__(self, db: Session):
        self.repository = DepartmentPerformanceAnalyticsRepository(db)

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(page, page_size, filters)
        except Exception as exc:
            logger.exception("Error during Department Research Performance Analytics retrieval: %s", exc)
            return {
                "items": [],
                "summary": {
                    "departments_analyzed": 0,
                    "active_faculty": 0,
                    "total_research_output": 0,
                    "publication_participation_rate": 0.0,
                    "papers_per_active_faculty": 0.0,
                    "average_department_health_score": 0.0,
                    "highest_performing_department": None,
                    "lowest_performing_department": None,
                    "total_funding": 0.0,
                },
                "charts": {
                    "health_score_by_department": [],
                    "output_distribution_by_department": [],
                    "funding_by_department": [],
                    "participation_rate_by_department": [],
                    "year_over_year_growth_by_department": [],
                },
                "page": page,
                "page_size": page_size,
                "total": 0,
            }
