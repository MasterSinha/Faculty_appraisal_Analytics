from typing import Any, Dict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.conferences_awards_analytics_repository import ConferencesAwardsAnalyticsRepository


class ConferencesAwardsAnalyticsService:
    """Service layer for Conferences and Awards Analytics with clean exception handling."""

    def __init__(self, db: Session):
        self.repository = ConferencesAwardsAnalyticsRepository(db)

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(filters)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Conferences and Awards Analytics service is temporarily unavailable. Verify database connection."
            ) from exc
        except Exception as exc:
            raise RuntimeError("An error occurred while processing conferences and awards analytics.") from exc
