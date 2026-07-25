from typing import Any, Dict, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.journals_analytics_repository import JournalsAnalyticsRepository


class JournalsAnalyticsService:
    """Service layer for Journal Publications Analytics with exception handling."""

    def __init__(self, db: Session):
        self.repository = JournalsAnalyticsRepository(db)

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.overview, filters)

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.departments, page, page_size, filters)

    def faculty(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.faculty, page, page_size, filters)

    def quality_indexing(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.quality_indexing, filters)

    def records(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.records, page, page_size, filters)

    def faculty_detail(self, faculty_email: str) -> Dict[str, Any]:
        return self._safe_call(self.repository.faculty_detail, faculty_email)

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.export_csv_rows, filters)

    @staticmethod
    def _safe_call(function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Journal Publications Analytics service is temporarily unavailable. Verify database connection."
            ) from exc
        except Exception as exc:
            raise RuntimeError("An error occurred while processing journal publications analytics.") from exc
