from typing import Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.research_analytics_repository import (
    AnalyticsSchemaError,
    ResearchAnalyticsRepository,
)


class ResearchAnalyticsService:
    def __init__(self, db: Session):
        self.repository = ResearchAnalyticsRepository(db)

    def inspect_schema(self) -> dict[str, Any]:
        return self._safe_call(self.repository.inspect_schema)

    def overview(self) -> dict[str, Any]:
        return self._safe_call(self.repository.overview)

    def indexing_distribution(self) -> list[dict[str, Any]]:
        return self._safe_call(self.repository.indexing_distribution)

    def faculty_summary(self, page: int, page_size: int, filters: dict[str, Any]) -> dict[str, Any]:
        return self._safe_call(self.repository.faculty_summary, page, page_size, filters)

    def faculty_detail(self, faculty_id: Any) -> dict[str, Any]:
        return self._safe_call(self.repository.faculty_detail, faculty_id)

    def publication_trend(self) -> list[dict[str, Any]]:
        return self._safe_call(self.repository.publication_trend)

    def projects_summary(self) -> dict[str, Any]:
        return self._safe_call(self.repository.projects_summary)

    def scores_comparison(self) -> dict[str, Any]:
        return self._safe_call(self.repository.scores_comparison)

    def top_faculty(self, limit: int) -> list[dict[str, Any]]:
        return self._safe_call(self.repository.top_faculty, limit)

    def top_journals(self, limit: int) -> list[dict[str, Any]]:
        return self._safe_call(self.repository.top_journals, limit)

    def filters(self) -> dict[str, Any]:
        return self._safe_call(self.repository.filters)

    def insights(self) -> list[dict[str, Any]]:
        return self._safe_call(self.repository.insights)

    def patents_summary(self) -> list[dict[str, Any]]:
        return self._safe_call(self.repository.patents_summary)

    def teaching_balance(self) -> list[dict[str, Any]]:
        return self._safe_call(self.repository.teaching_balance)

    def data_quality(self) -> list[dict[str, Any]]:
        return self._safe_call(self.repository.data_quality)

    def export_rows(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        return self.faculty_summary(1, 10000, filters)["items"]

    @staticmethod
    def _safe_call(function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (AnalyticsSchemaError, SQLAlchemyError) as exc:
            raise RuntimeError("Analytics data is unavailable. Check database connectivity and schema mapping.") from exc
