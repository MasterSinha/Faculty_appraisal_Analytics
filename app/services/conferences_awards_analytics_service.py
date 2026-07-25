import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.repositories.conferences_awards_analytics_repository import ConferencesAwardsAnalyticsRepository

logger = logging.getLogger(__name__)


class ConferencesAwardsAnalyticsService:
    """Service layer for Conferences and Awards Analytics with robust error resilience."""

    def __init__(self, db: Session):
        self.repository = ConferencesAwardsAnalyticsRepository(db)

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(filters)
        except Exception as exc:
            logger.exception("Error during Conferences and Awards Analytics retrieval: %s", exc)
            return {
                "conferences": [],
                "awards": [],
                "summary": {
                    "total_conference_papers": 0,
                    "international_conferences": 0,
                    "national_conferences": 0,
                    "total_awards": 0,
                    "participating_faculty": 0,
                    "participation_rate": 0.0,
                    "top_award_types": [],
                },
                "department_summary": [],
                "school_summary": [],
                "charts": {
                    "conference_level_distribution": [],
                    "award_category_breakdown": [],
                    "conferences_by_department": [],
                    "awards_by_school": [],
                    "trend_by_year": [],
                },
            }
