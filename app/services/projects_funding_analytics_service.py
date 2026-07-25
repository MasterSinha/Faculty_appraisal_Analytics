import logging
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.repositories.projects_funding_analytics_repository import ProjectsFundingAnalyticsRepository

logger = logging.getLogger(__name__)


class ProjectsFundingAnalyticsService:
    """Service layer for Projects and Funding Analytics with robust exception handling."""

    def __init__(self, db: Session):
        self.repository = ProjectsFundingAnalyticsRepository(db)

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.overview, filters, default={"total_projects": 0, "total_funding": 0.0, "total_proposals": 0})

    def projects(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.projects, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def external_projects(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.external_projects, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def proposals(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.proposals, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def funding_agencies(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.funding_agencies, filters, default=[])

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.departments, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def faculty(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.faculty, page, page_size, filters, default={"items": [], "page": page, "page_size": page_size, "total": 0})

    def trends(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.trends, filters, default={"trends": []})

    def concentration(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return self._safe_call(self.repository.concentration, filters, default={"agencies": []})

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._safe_call(self.repository.export_csv_rows, filters, default=[])

    @staticmethod
    def _safe_call(function, *args, default=None, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:
            logger.exception("Error in ProjectsFundingAnalyticsService: %s", exc)
            return default if default is not None else {"items": [], "total": 0, "page": 1, "page_size": 500}
