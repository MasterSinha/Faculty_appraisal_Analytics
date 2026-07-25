from typing import Any, Dict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.school_performance_analytics_repository import SchoolPerformanceAnalyticsRepository


class SchoolPerformanceAnalyticsService:
    """Service layer for School Research Performance Analytics with clean exception handling."""

    def __init__(self, db: Session):
        self.repository = SchoolPerformanceAnalyticsRepository(db)

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(page, page_size, filters)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "School Research Performance Analytics service is temporarily unavailable. Verify database connection."
            ) from exc
        except Exception as exc:
            raise RuntimeError("An error occurred while processing school research performance analytics.") from exc
