from typing import Any
from sqlalchemy.orm import Session

from app.repositories.faculty_research_analytics_repository import FacultyResearchAnalyticsRepository


class FacultyResearchAnalyticsService:
    def __init__(self, db: Session):
        self.repository = FacultyResearchAnalyticsRepository(db)

    def dashboard_summary(self, filters: dict[str, Any], refresh: bool = False) -> dict[str, Any]:
        return self.repository.dashboard_summary(filters, refresh=refresh)

    def overview(self, filters: dict[str, Any]) -> dict[str, Any]:
        res = self.repository.overview(filters)
        school_items = self.schools(filters, 1, 10000)["items"]
        res["publications_by_school"] = [
            {
                "school": row["school"],
                "journal_publications": row.get("journal_publications", 0),
                "total_journal_publications": row.get("journal_publications", 0),
                "total_research_papers": row.get("journal_publications", 0),
                "total_publications": row.get("journal_publications", 0),
                "publication_count": row.get("journal_publications", 0),
                "publications": row.get("journal_publications", 0),
                "total_papers": row.get("journal_publications", 0),
                "papers": row.get("journal_publications", 0),
            }
            for row in school_items
            if row.get("school")
        ]
        return res

    def departments(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        result = self.repository.departments(filters, page, page_size)
        for item in result.get("items", []):
            j_pubs = item.get("journal_publications", 0)
            item["total_journal_publications"] = j_pubs
            item["total_research_papers"] = j_pubs
            item["total_publications"] = j_pubs
            item["publication_count"] = j_pubs
            item["publications"] = j_pubs
            item["total_papers"] = j_pubs
            item["papers"] = j_pubs
        return result

    def schools(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        return self.repository.schools(filters, page, page_size)

    def faculty(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        return self.repository.faculty(filters, page, page_size)

    def faculty_detail(self, faculty_email: str, filters: dict[str, Any]) -> dict[str, Any]:
        return self.repository.faculty_detail(faculty_email, filters)

    def category_records(self, table: str, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        return self.repository.category_records(table, filters, page, page_size)

    def trends(self, filters: dict[str, Any]) -> dict[str, Any]:
        return self.repository.trends(filters)

    def insights(self, filters: dict[str, Any]) -> dict[str, list[str]]:
        return {"insights": self.repository.insights(filters)}

    def data_quality(self, filters: dict[str, Any]) -> dict[str, Any]:
        return self.repository.data_quality(filters)

    def filters(self) -> dict[str, Any]:
        return self.repository.filters()
