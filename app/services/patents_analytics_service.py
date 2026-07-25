import logging
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.repositories.patents_analytics_repository import PatentsAnalyticsRepository

logger = logging.getLogger(__name__)


class PatentsAnalyticsService:
    """Service layer for Patents and IPR Analytics with robust exception handling."""

    def __init__(self, db: Session):
        self.repository = PatentsAnalyticsRepository(db)

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.overview, filters, default={"total_patents": 0, "total_ipr": 0})

    def status_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.status_analytics, filters, default={"status_counts": []})

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.departments, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def faculty(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.faculty, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def records_patents(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.records_patents, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def records_ipr(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.records_ipr, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def trends(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.trends, filters, default={"trends": []})

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.export_csv_rows, filters, default=[])

    @staticmethod
    def _safe_call(function, *args, default=None, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:
            logger.exception("Error in PatentsAnalyticsService: %s", exc)
            return default if default is not None else {"items": [], "total": 0, "page": 1, "page_size": 500}
