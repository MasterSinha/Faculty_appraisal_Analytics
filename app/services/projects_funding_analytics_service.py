from typing import Any, Dict, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.projects_funding_analytics_repository import ProjectsFundingAnalyticsRepository


class ProjectsFundingAnalyticsService:
    """Service layer for Projects and Funding Analytics with clean exception handling."""

    def __init__(self, db: Session):
        self.repository = ProjectsFundingAnalyticsRepository(db)

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.overview, filters)

    def projects(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.projects, page, page_size, filters)

    def external_projects(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.external_projects, page, page_size, filters)

    def proposals(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.proposals, page, page_size, filters)

    def funding_agencies(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.funding_agencies, filters)

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.departments, page, page_size, filters)

    def faculty(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.faculty, page, page_size, filters)

    def trends(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.trends, filters)

    def concentration(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.concentration, filters)

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.export_csv_rows, filters)

    @staticmethod
    def _safe_call(function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "Projects and Funding Analytics service is temporarily unavailable. Verify database connection."
            ) from exc
        except Exception as exc:
            raise RuntimeError("An error occurred while processing projects and funding analytics.") from exc
