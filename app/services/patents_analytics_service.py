from typing import Any, Dict, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.patents_analytics_repository import PatentsAnalyticsRepository


class PatentsAnalyticsService:
    """Service layer for Patents and IPR Analytics with clean exception handling."""

    def __init__(self, db: Session):
        self.repository = PatentsAnalyticsRepository(db)

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.overview, filters)

    def status_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.status_analytics, filters)

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.departments, page, page_size, filters)

    def faculty(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.faculty, page, page_size, filters)

    def records_patents(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.records_patents, page, page_size, filters)

    def records_ipr(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.records_ipr, page, page_size, filters)

    def trends(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.trends, filters)

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.export_csv_rows, filters)

    @staticmethod
    def _safe_call(function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Patents and IPR Analytics service is temporarily unavailable. Verify database connection."
            ) from exc
        except Exception as exc:
            raise RuntimeError("An error occurred while processing patents and IPR analytics.") from exc
