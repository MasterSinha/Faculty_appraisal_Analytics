from typing import Any
from sqlalchemy.orm import Session

from app.repositories.faculty_research_analytics_repository import FacultyResearchAnalyticsRepository


class FacultyResearchAnalyticsService:
    def __init__(self, db: Session):
        self.repository = FacultyResearchAnalyticsRepository(db)

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
        departments = self.repository.departments(filters, 1, 10000)["items"]
        grouped: dict[str, dict[str, Any]] = {}
        for row in departments:
            school = row.get("school")
            if not school:
                continue
            target = grouped.setdefault(school, {"school": school})
            for key, value in row.items():
                if key in {"school", "department"}:
                    continue
                target[key] = target.get(key, 0) + (value or 0)

        for school_row in grouped.values():
            j_pubs = school_row.get("journal_publications", 0)
            school_row["total_journal_publications"] = j_pubs
            school_row["total_research_papers"] = j_pubs
            school_row["total_publications"] = j_pubs
            school_row["publication_count"] = j_pubs
            school_row["publications"] = j_pubs
            school_row["total_papers"] = j_pubs
            school_row["papers"] = j_pubs

        rows = sorted(grouped.values(), key=lambda item: item.get("journal_publications", 0), reverse=True)
        start = (page - 1) * page_size
        total_pages = (len(rows) + page_size - 1) // page_size if rows else 0
        return {"items": rows[start:start + page_size], "page": page, "page_size": page_size, "total": len(rows), "total_pages": total_pages}

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
