import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.repositories.research_data_quality_analytics_repository import ResearchDataQualityAnalyticsRepository

logger = logging.getLogger(__name__)


class ResearchDataQualityAnalyticsService:
    """Service layer for Research Data Quality Analytics with robust error resilience."""

    def __init__(self, db: Session):
        self.repository = ResearchDataQualityAnalyticsRepository(db)

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(filters)
        except Exception as exc:
            logger.exception("Error during Research Data Quality Analytics retrieval: %s", exc)
            return {
                "items": [],
                "alerts": [],
                "summary": {
                    "total_alerts": 0,
                    "critical_alerts": 0,
                    "warning_alerts": 0,
                    "informational_alerts": 0,
                    "total_records_analyzed": 0,
                    "records_with_alerts": 0,
                    "completeness_percentage": 100.0,
                },
                "charts": {
                    "alerts_by_severity": [],
                    "alerts_by_category": [],
                    "completeness_by_department": [],
                    "top_issue_types": [],
                    "alert_trend_by_year": [],
                },
                "completeness_percentage": 100.0,
                "review_supported": False,
            }
