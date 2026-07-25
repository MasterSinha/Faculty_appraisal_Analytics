from typing import Any, Dict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.research_data_quality_analytics_repository import ResearchDataQualityAnalyticsRepository


class ResearchDataQualityAnalyticsService:
    """Service layer for Research Data Quality Analytics with clean exception handling."""

    def __init__(self, db: Session):
        self.repository = ResearchDataQualityAnalyticsRepository(db)

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(filters)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Research Data Quality Analytics service is temporarily unavailable. Verify database connection."
            ) from exc
        except Exception as exc:
            raise RuntimeError("An error occurred while processing research data quality analytics.") from exc
