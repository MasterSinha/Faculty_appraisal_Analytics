from typing import Any, Dict, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.books_analytics_repository import BooksAnalyticsRepository
from app.repositories.research_analytics_repository import AnalyticsSchemaError


class BooksAnalyticsService:
    """Service layer for Books Analytics with clean exception handling."""

    def __init__(self, db: Session):
        self.repository = BooksAnalyticsRepository(db)

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.overview, filters)

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.departments, page, page_size, filters)

    def publishers(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.publishers, filters)

    def authorship(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.authorship, filters)

    def quality(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.quality, filters)

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
        except (AnalyticsSchemaError, SQLAlchemyError) as exc:
            raise RuntimeError("Books Analytics service is temporarily unavailable. Verify database connection.") from exc
