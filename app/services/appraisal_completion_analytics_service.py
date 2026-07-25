from typing import Any, Dict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.appraisal_completion_analytics_repository import AppraisalCompletionAnalyticsRepository


class AppraisalCompletionAnalyticsService:
    """Service layer for Appraisal Completion Analytics with clean exception handling."""

    def __init__(self, db: Session):
        self.repository = AppraisalCompletionAnalyticsRepository(db)

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(filters)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Appraisal Completion Analytics service is temporarily unavailable. Verify database connection."
            ) from exc
        except Exception as exc:
            raise RuntimeError("An error occurred while processing appraisal completion analytics.") from exc
