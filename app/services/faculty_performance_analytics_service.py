from typing import Any, Dict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.faculty_performance_analytics_repository import FacultyPerformanceAnalyticsRepository


class FacultyPerformanceAnalyticsService:
    """Service layer for Faculty Research Performance Analytics with clean exception handling."""

    def __init__(self, db: Session):
        self.repository = FacultyPerformanceAnalyticsRepository(db)

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(page, page_size, filters)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Faculty Research Performance Analytics service is temporarily unavailable. Verify database connection."
            ) from exc
        except Exception as exc:
            raise RuntimeError("An error occurred while processing faculty research performance analytics.") from exc
