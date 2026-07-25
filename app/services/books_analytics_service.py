import logging
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.repositories.books_analytics_repository import BooksAnalyticsRepository

logger = logging.getLogger(__name__)


class BooksAnalyticsService:
    """Service layer for Books Analytics with robust exception handling."""

    def __init__(self, db: Session):
        self.repository = BooksAnalyticsRepository(db)

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.overview, filters, default={"total_books": 0})

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.departments, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def publishers(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.publishers, filters, default=[])

    def authorship(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.authorship, filters, default={"authorship_breakdown": []})

    def quality(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.quality, filters, default={"quality_breakdown": []})

    def records(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.records, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def faculty_detail(self, faculty_email: str) -> Dict[str, Any]:
        return self._safe_call(self.repository.faculty_detail, faculty_email, default={"profile": {}, "records": []})

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.export_csv_rows, filters, default=[])

    @staticmethod
    def _safe_call(function, *args, default=None, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:
            logger.exception("Error in BooksAnalyticsService: %s", exc)
            return default if default is not None else {"items": [], "total": 0, "page": 1, "page_size": 500}
