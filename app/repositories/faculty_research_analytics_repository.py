from math import ceil
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class FacultyResearchAnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def overview(self, filters: dict[str, Any]) -> dict[str, Any]:
        where, params = self._where(filters, alias="fp")
        sql = text(f"""
            WITH active_faculty AS (
                SELECT DISTINCT fp.email
                FROM faculty_profiles fp
                WHERE fp.is_active = TRUE {where}
            ),
            journals AS (
                SELECT jp.*
                FROM journal_publications jp
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email))
                WHERE fp.is_active = TRUE AND NULLIF(TRIM(jp.title), '') IS NOT NULL {where}
            ),
            books AS (
                SELECT bp.*
                FROM book_publications bp
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(bp.faculty_email))
                WHERE fp.is_active = TRUE
                  AND COALESCE(NULLIF(TRIM(bp.title), ''), NULLIF(TRIM(bp.book), '')) IS NOT NULL {where}
            ),
            patents_valid AS (
                SELECT p.*
                FROM patents p
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email))
                WHERE fp.is_active = TRUE AND NULLIF(TRIM(p.title), '') IS NOT NULL {where}
            ),
            projects AS (
                SELECT rp.faculty_email, rp.academic_year, rp.amount, rp.project_status, rp.agency, rp.title, FALSE AS external_project
                FROM research_projects rp
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email))
                WHERE fp.is_active = TRUE AND NULLIF(TRIM(rp.title), '') IS NOT NULL {where}
                UNION ALL
                SELECT erp.faculty_email, erp.academic_year, erp.amount, erp.project_status, erp.agency, erp.title, TRUE AS external_project
                FROM external_research_projects erp
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(erp.faculty_email))
                WHERE fp.is_active = TRUE AND NULLIF(TRIM(erp.title), '') IS NOT NULL {where}
            ),
            proposals AS (
                SELECT rpr.*
                FROM research_proposals rpr
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rpr.faculty_email))
                WHERE fp.is_active = TRUE AND NULLIF(TRIM(rpr.title), '') IS NOT NULL {where}
            )
            SELECT
                (SELECT COUNT(*) FROM active_faculty) AS total_active_faculty,
                (SELECT COUNT(*) FROM journals) AS total_journal_publications,
                (SELECT COUNT(DISTINCT LOWER(TRIM(faculty_email))) FROM journals) AS faculty_with_journal_publication,
                (SELECT COUNT(*) FROM books) AS total_book_publications,
                (SELECT COUNT(DISTINCT LOWER(TRIM(faculty_email))) FROM books) AS faculty_with_book_publication,
                (SELECT COUNT(*) FROM patents_valid) AS total_patents,
                (SELECT COUNT(*) FROM patents_valid WHERE LOWER(COALESCE(patent_status, '')) LIKE '%grant%') AS patents_granted,
                (SELECT COUNT(*) FROM projects) AS total_research_projects,
                (SELECT COALESCE(SUM(amount), 0) FROM projects) AS total_sanctioned_funding,
                (SELECT COUNT(*) FROM projects WHERE external_project = TRUE) AS external_funded_projects,
                (SELECT COALESCE(SUM(amount), 0) FROM projects WHERE external_project = TRUE) AS external_funded_amount,
                (SELECT COUNT(*) FROM proposals) AS total_research_proposals,
                (SELECT COALESCE(SUM(amount), 0) FROM proposals) AS total_proposal_amount,
                (SELECT COUNT(*) FROM research_guidance rg JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rg.faculty_email)) WHERE fp.is_active = TRUE {where}) AS total_research_scholars_guided,
                (SELECT COUNT(*) FROM conferences c JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(c.faculty_email)) WHERE fp.is_active = TRUE AND NULLIF(TRIM(c.title), '') IS NOT NULL {where}) AS total_conferences,
                (SELECT COUNT(*) FROM awards a JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(a.faculty_email)) WHERE fp.is_active = TRUE AND NULLIF(TRIM(a.title), '') IS NOT NULL {where}) AS total_awards,
                (SELECT COUNT(*) FROM products_developed pd JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(pd.faculty_email)) WHERE fp.is_active = TRUE AND NULLIF(TRIM(pd.details), '') IS NOT NULL {where}) AS total_products_developed
        """)
        row = dict(self.db.execute(sql, params).mappings().one())
        total_active = row["total_active_faculty"] or 0
        publishing = row["faculty_with_journal_publication"] or 0
        journals = row["total_journal_publications"] or 0
        funding = float(row["total_sanctioned_funding"] or 0)
        row["publication_participation_rate"] = round((publishing / total_active) * 100, 2) if total_active else 0
        row["average_publications_per_publishing_faculty"] = round(journals / publishing, 2) if publishing else 0
        row["funding_per_active_faculty"] = round(funding / total_active, 2) if total_active else 0
        return row

    def departments(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        where, params = self._where(filters)
        base = f"""
            WITH summary AS (
                SELECT
                    fp.school,
                    fp.department,
                    COUNT(DISTINCT fp.email) FILTER (WHERE fp.is_active = TRUE) AS total_active_faculty,
                    COUNT(DISTINCT jp.id) FILTER (WHERE NULLIF(TRIM(jp.title), '') IS NOT NULL) AS journal_publications,
                    COUNT(DISTINCT jp.faculty_email) FILTER (WHERE NULLIF(TRIM(jp.title), '') IS NOT NULL) AS faculty_who_published_papers,
                    COUNT(DISTINCT bp.id) FILTER (WHERE COALESCE(NULLIF(TRIM(bp.title), ''), NULLIF(TRIM(bp.book), '')) IS NOT NULL) AS book_publications,
                    COUNT(DISTINCT bp.faculty_email) FILTER (WHERE COALESCE(NULLIF(TRIM(bp.title), ''), NULLIF(TRIM(bp.book), '')) IS NOT NULL) AS faculty_who_published_books,
                    COUNT(DISTINCT p.id) FILTER (WHERE NULLIF(TRIM(p.title), '') IS NOT NULL) AS patents,
                    COUNT(DISTINCT p.id) FILTER (WHERE LOWER(COALESCE(p.patent_status, '')) LIKE '%grant%') AS patents_granted,
                    COUNT(DISTINCT rp.id) FILTER (WHERE NULLIF(TRIM(rp.title), '') IS NOT NULL) AS research_projects,
                    COALESCE(SUM(DISTINCT rp.amount), 0) AS total_project_funding,
                    COUNT(DISTINCT rpr.id) FILTER (WHERE NULLIF(TRIM(rpr.title), '') IS NOT NULL) AS research_proposals,
                    COALESCE(SUM(DISTINCT rpr.amount), 0) AS total_proposal_amount,
                    COUNT(DISTINCT rg.id) AS research_scholars_guided,
                    COUNT(DISTINCT c.id) FILTER (WHERE NULLIF(TRIM(c.title), '') IS NOT NULL) AS conferences,
                    COUNT(DISTINCT a.id) FILTER (WHERE NULLIF(TRIM(a.title), '') IS NOT NULL) AS awards,
                    COUNT(DISTINCT pd.id) FILTER (WHERE NULLIF(TRIM(pd.details), '') IS NOT NULL) AS products_developed,
                    COALESCE(SUM(DISTINCT jp.score), 0)
                      + COALESCE(SUM(DISTINCT bp.score), 0)
                      + COALESCE(SUM(DISTINCT p.score), 0)
                      + COALESCE(SUM(DISTINCT rp.score), 0) AS total_research_score
                FROM faculty_profiles fp
                LEFT JOIN journal_publications jp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email)) AND fp.academic_year = jp.academic_year
                LEFT JOIN book_publications bp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(bp.faculty_email)) AND fp.academic_year = bp.academic_year
                LEFT JOIN patents p ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email)) AND fp.academic_year = p.academic_year
                LEFT JOIN research_projects rp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email)) AND fp.academic_year = rp.academic_year
                LEFT JOIN research_proposals rpr ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rpr.faculty_email)) AND fp.academic_year = rpr.academic_year
                LEFT JOIN research_guidance rg ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rg.faculty_email)) AND fp.academic_year = rg.academic_year
                LEFT JOIN conferences c ON LOWER(TRIM(fp.email)) = LOWER(TRIM(c.faculty_email)) AND fp.academic_year = c.academic_year
                LEFT JOIN awards a ON LOWER(TRIM(fp.email)) = LOWER(TRIM(a.faculty_email)) AND fp.academic_year = a.academic_year
                LEFT JOIN products_developed pd ON LOWER(TRIM(fp.email)) = LOWER(TRIM(pd.faculty_email)) AND fp.academic_year = pd.academic_year
                WHERE fp.is_active = TRUE {where}
                GROUP BY fp.school, fp.department
            )
        """
        return self._paginate(base, "SELECT *, ROUND((faculty_who_published_papers::numeric / NULLIF(total_active_faculty, 0)) * 100, 2) AS publication_participation_percentage FROM summary ORDER BY journal_publications DESC", params, page, page_size)

    def faculty(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        where, params = self._where(filters, alias="fp")
        sql = f"""
            WITH activity AS (
                SELECT fp.email AS faculty_email, fp.employee_id, fp.full_name, fp.school, fp.department, fp.designation,
                       COUNT(DISTINCT jp.id) FILTER (WHERE NULLIF(TRIM(jp.title), '') IS NOT NULL) AS journal_publications,
                       COUNT(DISTINCT bp.id) FILTER (WHERE COALESCE(NULLIF(TRIM(bp.title), ''), NULLIF(TRIM(bp.book), '')) IS NOT NULL) AS book_publications,
                       COUNT(DISTINCT p.id) FILTER (WHERE NULLIF(TRIM(p.title), '') IS NOT NULL) AS patents,
                       COUNT(DISTINCT rp.id) FILTER (WHERE NULLIF(TRIM(rp.title), '') IS NOT NULL) AS research_projects,
                       COALESCE(SUM(DISTINCT rp.amount), 0) AS project_funding,
                       COUNT(DISTINCT rpr.id) FILTER (WHERE NULLIF(TRIM(rpr.title), '') IS NOT NULL) AS proposals,
                       COUNT(DISTINCT rg.id) AS research_guidance,
                       COUNT(DISTINCT c.id) FILTER (WHERE NULLIF(TRIM(c.title), '') IS NOT NULL) AS conferences,
                       COUNT(DISTINCT a.id) FILTER (WHERE NULLIF(TRIM(a.title), '') IS NOT NULL) AS awards,
                       COUNT(DISTINCT pd.id) FILTER (WHERE NULLIF(TRIM(pd.details), '') IS NOT NULL) AS products_developed,
                       COALESCE(SUM(DISTINCT jp.score), 0) + COALESCE(SUM(DISTINCT bp.score), 0) + COALESCE(SUM(DISTINCT p.score), 0) + COALESCE(SUM(DISTINCT rp.score), 0) AS total_research_score
                FROM faculty_profiles fp
                LEFT JOIN journal_publications jp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email)) AND fp.academic_year = jp.academic_year
                LEFT JOIN book_publications bp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(bp.faculty_email)) AND fp.academic_year = bp.academic_year
                LEFT JOIN patents p ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email)) AND fp.academic_year = p.academic_year
                LEFT JOIN research_projects rp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email)) AND fp.academic_year = rp.academic_year
                LEFT JOIN research_proposals rpr ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rpr.faculty_email)) AND fp.academic_year = rpr.academic_year
                LEFT JOIN research_guidance rg ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rg.faculty_email)) AND fp.academic_year = rg.academic_year
                LEFT JOIN conferences c ON LOWER(TRIM(fp.email)) = LOWER(TRIM(c.faculty_email)) AND fp.academic_year = c.academic_year
                LEFT JOIN awards a ON LOWER(TRIM(fp.email)) = LOWER(TRIM(a.faculty_email)) AND fp.academic_year = a.academic_year
                LEFT JOIN products_developed pd ON LOWER(TRIM(fp.email)) = LOWER(TRIM(pd.faculty_email)) AND fp.academic_year = pd.academic_year
                WHERE fp.is_active = TRUE {where}
                GROUP BY fp.email, fp.employee_id, fp.full_name, fp.school, fp.department, fp.designation
            )
        """
        return self._paginate(sql, "SELECT *, journal_publications + book_publications + patents + research_projects + proposals + research_guidance + conferences + awards + products_developed AS total_research_contribution_count FROM activity ORDER BY total_research_score DESC", params, page, page_size)

    def faculty_detail(self, faculty_email: str, filters: dict[str, Any]) -> dict[str, Any]:
        filters = {**filters, "faculty_email": faculty_email}
        _, params = self._where(filters)
        params["faculty_email"] = faculty_email
        profile = self.db.execute(text("""
            SELECT email, employee_id, full_name, qualification, designation, department, school, academic_year, appraisal_role, is_active
            FROM faculty_profiles
            WHERE LOWER(TRIM(email)) = LOWER(TRIM(:faculty_email))
            LIMIT 1
        """), params).mappings().first()
        return {
            "profile": dict(profile) if profile else {"email": faculty_email},
            "journals": self._records("journal_publications", filters),
            "books": self._records("book_publications", filters),
            "patents": self._records("patents", filters),
            "projects": self._records("research_projects", filters),
            "external_projects": self._records("external_research_projects", filters),
            "proposals": self._records("research_proposals", filters),
            "guidance": self._records("research_guidance", filters),
            "conferences": self._records("conferences", filters),
            "awards": self._records("awards", filters),
            "products": self._records("products_developed", filters),
        }

    def category_records(self, table: str, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        where, params = self._where(filters, alias="fp")
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        sql = text(f"""
            SELECT t.*, fp.full_name, fp.employee_id, fp.school, fp.department, fp.designation
            FROM {table} t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE {where}
            ORDER BY t.academic_year DESC
            LIMIT :limit OFFSET :offset
        """)
        count_sql = text(f"""
            SELECT COUNT(*) FROM {table} t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE {where}
        """)
        total = int(self.db.execute(count_sql, params).scalar() or 0)
        return {"items": [dict(row) for row in self.db.execute(sql, params).mappings()], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}

    def trends(self, filters: dict[str, Any]) -> dict[str, Any]:
        where, params = self._where(filters, alias="fp")
        rows = self.db.execute(text(f"""
            SELECT jp.academic_year, COUNT(DISTINCT jp.id) AS journal_publications
            FROM journal_publications jp
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email))
            WHERE fp.is_active = TRUE AND NULLIF(TRIM(jp.title), '') IS NOT NULL {where}
            GROUP BY jp.academic_year
            ORDER BY jp.academic_year
        """), params).mappings()
        return {"publications_by_academic_year": [dict(row) for row in rows]}

    def data_quality(self, filters: dict[str, Any]) -> dict[str, Any]:
        checks = {
            "publications_with_missing_titles": "SELECT COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(title), '') IS NULL",
            "books_with_missing_isbn": "SELECT COUNT(*) FROM book_publications WHERE NULLIF(TRIM(isbn), '') IS NULL",
            "journal_publications_with_missing_issn": "SELECT COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(issn), '') IS NULL",
            "publications_with_missing_indexing": "SELECT COUNT(*) FROM journal_publications WHERE NULLIF(TRIM(indexing), '') IS NULL",
            "patents_with_missing_status": "SELECT COUNT(*) FROM patents WHERE NULLIF(TRIM(patent_status), '') IS NULL",
            "projects_with_missing_funding_amount": "SELECT COUNT(*) FROM research_projects WHERE amount IS NULL",
            "records_without_matching_faculty_email": "SELECT COUNT(*) FROM journal_publications jp LEFT JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email)) WHERE fp.email IS NULL",
            "blank_or_null_departments": "SELECT COUNT(*) FROM faculty_profiles WHERE NULLIF(TRIM(department), '') IS NULL",
            "unknown_academic_years": "SELECT COUNT(*) FROM faculty_profiles WHERE NULLIF(TRIM(academic_year), '') IS NULL",
        }
        return {name: int(self.db.execute(text(sql)).scalar() or 0) for name, sql in checks.items()}

    def insights(self, filters: dict[str, Any]) -> list[str]:
        overview = self.overview(filters)
        departments = self.departments(filters, 1, 5)["items"]
        insights = []
        if departments:
            top_department = departments[0]
            insights.append(f"{top_department.get('department') or 'Unknown department'} produced the highest journal publication output.")
        insights.append(f"{overview['publication_participation_rate']}% of active faculty published at least one journal paper.")
        if overview["total_active_faculty"]:
            insights.append(f"Funding per active faculty is INR {overview['funding_per_active_faculty']:,.0f}.")
        if overview["external_funded_amount"] and overview["total_sanctioned_funding"]:
            share = (overview["external_funded_amount"] / overview["total_sanctioned_funding"]) * 100
            insights.append(f"External funded projects account for {share:.1f}% of sanctioned research funding.")
        return insights

    def filters(self) -> dict[str, Any]:
        return {
            "academic_years": self._distinct("faculty_profiles", "academic_year"),
            "schools": self._distinct("faculty_profiles", "school"),
            "departments": self._distinct("faculty_profiles", "department"),
            "designations": self._distinct("faculty_profiles", "designation"),
            "indexing": self._distinct("journal_publications", "indexing"),
            "patent_statuses": self._distinct("patents", "patent_status"),
            "project_statuses": self._distinct("research_projects", "project_status"),
            "funding_agencies": self._distinct("research_projects", "agency"),
        }

    def _records(self, table: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where, params = self._where(filters, alias="fp")
        sql = text(f"""
            SELECT t.*
            FROM {table} t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE 1 = 1 {where}
            ORDER BY t.academic_year DESC
            LIMIT 200
        """)
        return [dict(row) for row in self.db.execute(sql, params).mappings()]

    def _paginate(self, with_sql: str, select_sql: str, params: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
        count = int(self.db.execute(text(f"{with_sql} SELECT COUNT(*) FROM ({select_sql}) counted"), params).scalar() or 0)
        rows = self.db.execute(text(f"{with_sql} {select_sql} LIMIT :limit OFFSET :offset"), params).mappings()
        return {"items": [dict(row) for row in rows], "page": page, "page_size": page_size, "total": count, "total_pages": ceil(count / page_size) if count else 0}

    def _where(self, filters: dict[str, Any], alias: str = "fp") -> tuple[str, dict[str, Any]]:
        clauses = []
        params: dict[str, Any] = {}
        for key in ("academic_year", "school", "department", "designation"):
            if filters.get(key):
                clauses.append(f"AND {alias}.{key} = :{key}")
                params[key] = filters[key]
        if filters.get("faculty_email"):
            clauses.append(f"AND LOWER(TRIM({alias}.email)) = LOWER(TRIM(:faculty_email))")
            params["faculty_email"] = filters["faculty_email"]
        return " ".join(clauses), params

    def _distinct(self, table: str, column: str) -> list[Any]:
        sql = text(f"SELECT DISTINCT {column} FROM {table} WHERE NULLIF(TRIM({column}::text), '') IS NOT NULL ORDER BY {column}")
        return [row[0] for row in self.db.execute(sql).all()]
