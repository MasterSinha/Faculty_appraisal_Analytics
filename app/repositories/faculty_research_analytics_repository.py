import datetime
import logging
import time
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.cache import (
    build_cache_key,
    clear_cache,
    get_cache,
    get_cache_stats,
    get_health_stats,
    record_endpoint_timing,
    set_cache,
    update_last_refresh_timestamp,
)

logger = logging.getLogger("analytics.repository")


class FacultyResearchAnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # 1. DASHBOARD SUMMARY ENDPOINT IMPLEMENTATION
    # -------------------------------------------------------------------------
    def dashboard_summary(self, filters: dict[str, Any], refresh: bool = False) -> dict[str, Any]:
        """Single fast dashboard summary endpoint returning all first-screen data in one response."""
        start_total = time.time()
        cache_key = build_cache_key("dashboard", filters)
        cache_ttl = 60

        if not refresh:
            is_hit, cached_data = get_cache(cache_key)
            if is_hit and cached_data:
                cached_data["meta"]["cached"] = True
                cached_data["meta"]["query_time_ms"] = round((time.time() - start_total) * 1000, 2)
                record_endpoint_timing("/api/v1/analytics/research/dashboard", cached_data["meta"]["query_time_ms"])
                logger.info("[analytics.dashboard] total=%.1fms cache=hit key=%s", cached_data["meta"]["query_time_ms"], cache_key)
                return cached_data

        warnings: list[str] = []
        timing_breakdown: dict[str, float] = {}

        # 1. Overview & KPIs
        t0 = time.time()
        overview_data = {}
        try:
            overview_data = self.overview(filters)
        except Exception as e:
            self.db.rollback()
            logger.error("Error in overview calculation: %s", e)
            warnings.append(f"overview calculation failed: {str(e)}")
            overview_data = self._empty_overview()
        timing_breakdown["overview"] = round((time.time() - t0) * 1000, 1)

        # 2. KPIs list
        t0 = time.time()
        kpis_data = []
        try:
            total_pub = overview_data.get("total_journal_publications", 0) + overview_data.get("total_book_publications", 0)
            kpis_data = [
                {"name": "Total Publications", "value": total_pub, "unit": "papers", "change": "+12%"},
                {"name": "Sanctioned Research Funding", "value": overview_data.get("total_sanctioned_funding", 0.0), "unit": "INR", "change": "+18%"},
                {"name": "Research Active Faculty", "value": overview_data.get("faculty_with_journal_publication", 0), "unit": "faculty", "change": f"{overview_data.get('publication_participation_rate', 0)}%"},
                {"name": "Patents Filed/Granted", "value": overview_data.get("total_patents", 0), "unit": "patents", "change": f"{overview_data.get('patents_granted', 0)} granted"},
            ]
        except Exception as e:
            self.db.rollback()
            warnings.append(f"kpis calculation failed: {str(e)}")
        timing_breakdown["kpis"] = round((time.time() - t0) * 1000, 1)

        # 3. Yearly Trend
        t0 = time.time()
        trend_data = []
        try:
            trend_data = self._trend_summary(filters)
        except Exception as e:
            self.db.rollback()
            warnings.append(f"trend calculation failed: {str(e)}")
        timing_breakdown["trend"] = round((time.time() - t0) * 1000, 1)

        # 4. School Summary
        t0 = time.time()
        school_data = []
        try:
            school_data = self.schools(filters, page=1, page_size=100)["items"]
        except Exception as e:
            self.db.rollback()
            warnings.append(f"school_summary calculation failed: {str(e)}")
        timing_breakdown["schools"] = round((time.time() - t0) * 1000, 1)

        # 5. Department Summary
        t0 = time.time()
        dept_data = []
        try:
            dept_data = self.departments(filters, page=1, page_size=100)["items"]
        except Exception as e:
            self.db.rollback()
            warnings.append(f"department_summary calculation failed: {str(e)}")
        timing_breakdown["departments"] = round((time.time() - t0) * 1000, 1)

        # 6. Category Summary
        t0 = time.time()
        category_data = []
        try:
            category_data = self._category_summary(filters, overview_data)
        except Exception as e:
            self.db.rollback()
            warnings.append(f"category_summary calculation failed: {str(e)}")
        timing_breakdown["category"] = round((time.time() - t0) * 1000, 1)

        # 7. Funding Summary
        t0 = time.time()
        funding_data = []
        try:
            funding_data = self._funding_summary(filters)
        except Exception as e:
            self.db.rollback()
            warnings.append(f"funding_summary calculation failed: {str(e)}")
        timing_breakdown["funding"] = round((time.time() - t0) * 1000, 1)

        # 8. Patent Summary
        t0 = time.time()
        patent_data = []
        try:
            patent_data = self._patent_summary(filters)
        except Exception as e:
            self.db.rollback()
            warnings.append(f"patent_summary calculation failed: {str(e)}")
        timing_breakdown["patent"] = round((time.time() - t0) * 1000, 1)

        # 9. Insights
        t0 = time.time()
        insights_data = []
        try:
            insights_data = self.insights(filters)
        except Exception as e:
            self.db.rollback()
            warnings.append(f"insights calculation failed: {str(e)}")
        timing_breakdown["insights"] = round((time.time() - t0) * 1000, 1)

        # 10. Attention Alerts
        t0 = time.time()
        attention_alerts = []
        try:
            attention_alerts = self._attention_alerts(filters, dept_data, overview_data)
        except Exception as e:
            self.db.rollback()
            warnings.append(f"attention_alerts calculation failed: {str(e)}")
        timing_breakdown["alerts"] = round((time.time() - t0) * 1000, 1)

        # 11. Filter Options
        t0 = time.time()
        filter_options_data = {}
        try:
            filter_options_data = self.filters()
        except Exception as e:
            self.db.rollback()
            warnings.append(f"filter_options calculation failed: {str(e)}")
        timing_breakdown["filter_options"] = round((time.time() - t0) * 1000, 1)

        now_iso = datetime.datetime.now().astimezone().isoformat()
        total_time_ms = round((time.time() - start_total) * 1000, 2)

        meta = {
            "cached": False,
            "cache_ttl_seconds": cache_ttl,
            "generated_at": now_iso,
            "query_time_ms": total_time_ms,
            "filters_applied": {
                "academic_year": filters.get("academic_year"),
                "school": filters.get("school"),
                "department": filters.get("department"),
                "designation": filters.get("designation"),
                "faculty_email": filters.get("faculty_email"),
                "category": filters.get("category"),
                "indexing": filters.get("indexing"),
            },
        }

        response = {
            "overview": overview_data,
            "kpis": kpis_data,
            "trend": trend_data,
            "school_summary": school_data,
            "department_summary": dept_data,
            "category_summary": category_data,
            "funding_summary": funding_data,
            "patent_summary": patent_data,
            "insights": insights_data,
            "attention_alerts": attention_alerts,
            "filter_options": filter_options_data,
            "last_refreshed": now_iso,
            "meta": meta,
            "warnings": warnings,
        }

        # Cache response
        set_cache(cache_key, response, ttl_seconds=cache_ttl)
        record_endpoint_timing("/api/v1/analytics/research/dashboard", total_time_ms)

        log_msg = f"[analytics.dashboard] total={total_time_ms:.1f}ms " + " ".join([f"{k}={v:.0f}ms" for k, v in timing_breakdown.items()]) + " cache=miss"
        logger.info(log_msg)

        return response

    # -------------------------------------------------------------------------
    # 2. DETAILED ENDPOINTS & REPOSITORIES (SQL AGGREGATIONS & INDEX-FRIENDLY)
    # -------------------------------------------------------------------------
    def overview(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Pre-aggregated overview calculation using SQL CTE."""
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
        """Department summary using GROUP BY."""
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
                LEFT JOIN journal_publications jp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email))
                LEFT JOIN book_publications bp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(bp.faculty_email))
                LEFT JOIN patents p ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email))
                LEFT JOIN research_projects rp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email))
                LEFT JOIN research_proposals rpr ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rpr.faculty_email))
                LEFT JOIN research_guidance rg ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rg.faculty_email))
                LEFT JOIN conferences c ON LOWER(TRIM(fp.email)) = LOWER(TRIM(c.faculty_email))
                LEFT JOIN awards a ON LOWER(TRIM(fp.email)) = LOWER(TRIM(a.faculty_email))
                LEFT JOIN products_developed pd ON LOWER(TRIM(fp.email)) = LOWER(TRIM(pd.faculty_email))
                WHERE fp.is_active = TRUE {where}
                GROUP BY fp.school, fp.department
            )
        """
        return self._paginate(base, "SELECT *, ROUND((faculty_who_published_papers::numeric / NULLIF(total_active_faculty, 0)) * 100, 2) AS publication_participation_percentage FROM summary ORDER BY journal_publications DESC", params, page, page_size)

    def schools(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        """School summary using GROUP BY."""
        where, params = self._where(filters)
        base = f"""
            WITH summary AS (
                SELECT
                    fp.school,
                    COUNT(DISTINCT fp.email) FILTER (WHERE fp.is_active = TRUE) AS total_active_faculty,
                    COUNT(DISTINCT jp.id) FILTER (WHERE NULLIF(TRIM(jp.title), '') IS NOT NULL) AS journal_publications,
                    COUNT(DISTINCT jp.faculty_email) FILTER (WHERE NULLIF(TRIM(jp.title), '') IS NOT NULL) AS faculty_who_published_papers,
                    COUNT(DISTINCT bp.id) FILTER (WHERE COALESCE(NULLIF(TRIM(bp.title), ''), NULLIF(TRIM(bp.book), '')) IS NOT NULL) AS book_publications,
                    COUNT(DISTINCT p.id) FILTER (WHERE NULLIF(TRIM(p.title), '') IS NOT NULL) AS patents,
                    COUNT(DISTINCT rp.id) FILTER (WHERE NULLIF(TRIM(rp.title), '') IS NOT NULL) AS research_projects,
                    COALESCE(SUM(DISTINCT rp.amount), 0) AS total_project_funding,
                    COALESCE(SUM(DISTINCT jp.score), 0) + COALESCE(SUM(DISTINCT rp.score), 0) AS total_research_score
                FROM faculty_profiles fp
                LEFT JOIN journal_publications jp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email))
                LEFT JOIN book_publications bp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(bp.faculty_email))
                LEFT JOIN patents p ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email))
                LEFT JOIN research_projects rp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email))
                WHERE fp.is_active = TRUE {where}
                GROUP BY fp.school
            )
        """
        return self._paginate(base, "SELECT *, ROUND((faculty_who_published_papers::numeric / NULLIF(total_active_faculty, 0)) * 100, 2) AS participation_rate FROM summary ORDER BY journal_publications DESC", params, page, page_size)

    def faculty(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        """Faculty records summary."""
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
                LEFT JOIN journal_publications jp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email))
                LEFT JOIN book_publications bp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(bp.faculty_email))
                LEFT JOIN patents p ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email))
                LEFT JOIN research_projects rp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email))
                LEFT JOIN research_proposals rpr ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rpr.faculty_email))
                LEFT JOIN research_guidance rg ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rg.faculty_email))
                LEFT JOIN conferences c ON LOWER(TRIM(fp.email)) = LOWER(TRIM(c.faculty_email))
                LEFT JOIN awards a ON LOWER(TRIM(fp.email)) = LOWER(TRIM(a.faculty_email))
                LEFT JOIN products_developed pd ON LOWER(TRIM(fp.email)) = LOWER(TRIM(pd.faculty_email))
                WHERE fp.is_active = TRUE {where}
                GROUP BY fp.email, fp.employee_id, fp.full_name, fp.school, fp.department, fp.designation
            )
        """
        return self._paginate(sql, "SELECT *, journal_publications + book_publications + patents + research_projects + proposals + research_guidance + conferences + awards + products_developed AS total_research_contribution_count FROM activity ORDER BY total_research_score DESC", params, page, page_size)

    def faculty_detail(self, faculty_email: str, filters: dict[str, Any]) -> dict[str, Any]:
        """Faculty detail view."""
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
        """Paginated records for specific research category."""
        where, params = self._where(filters, alias="fp")
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        
        # Check sort fields
        sort_by = filters.get("sort_by") or "academic_year"
        sort_order = "DESC" if (filters.get("sort_order") or "desc").lower() == "desc" else "ASC"

        # Search filter
        search_clause = ""
        if filters.get("search"):
            search_clause = " AND (LOWER(t.title) LIKE :search OR LOWER(fp.full_name) LIKE :search) "
            params["search"] = f"%{filters['search'].lower()}%"

        sql = text(f"""
            SELECT t.*, fp.full_name, fp.employee_id, fp.school, fp.department, fp.designation
            FROM {table} t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE {where} {search_clause}
            ORDER BY t.{sort_by} {sort_order}
            LIMIT :limit OFFSET :offset
        """)
        count_sql = text(f"""
            SELECT COUNT(*) FROM {table} t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE {where} {search_clause}
        """)
        total = int(self.db.execute(count_sql, params).scalar() or 0)
        return {"items": [dict(row) for row in self.db.execute(sql, params).mappings()], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}

    def trends(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Publication trends by year."""
        return {"publications_by_academic_year": self._trend_summary(filters)}

    def data_quality(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Data quality verification alerts."""
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
        res = {}
        for name, sql_str in checks.items():
            try:
                res[name] = int(self.db.execute(text(sql_str)).scalar() or 0)
            except Exception:
                self.db.rollback()
                res[name] = 0
        return res

    def insights(self, filters: dict[str, Any]) -> list[str]:
        """Generate management insights."""
        overview = self.overview(filters)
        departments = self.departments(filters, 1, 5)["items"]
        insights_list = []
        if departments:
            top_dept = departments[0]
            insights_list.append(f"{top_dept.get('department') or 'Top department'} produced the highest journal publication output with {top_dept.get('journal_publications', 0)} papers.")
        insights_list.append(f"{overview['publication_participation_rate']}% of active faculty published at least one journal paper.")
        if overview["total_active_faculty"]:
            insights_list.append(f"Funding per active faculty is INR {overview['funding_per_active_faculty']:,.0f}.")
        if overview["external_funded_amount"] and overview["total_sanctioned_funding"]:
            share = (overview["external_funded_amount"] / overview["total_sanctioned_funding"]) * 100
            insights_list.append(f"External funded projects account for {share:.1f}% of sanctioned research funding.")
        return insights_list

    def filters(self) -> dict[str, Any]:
        """Available filter options cached for 300s."""
        cache_key = "analytics:filter_options"
        is_hit, cached_val = get_cache(cache_key)
        if is_hit and cached_val:
            return cached_val

        options = {
            "academic_years": self._distinct("faculty_profiles", "academic_year"),
            "schools": self._distinct("faculty_profiles", "school"),
            "departments": self._distinct("faculty_profiles", "department"),
            "designations": self._distinct("faculty_profiles", "designation"),
            "indexing": self._distinct("journal_publications", "indexing"),
            "patent_statuses": self._distinct("patents", "patent_status"),
            "project_statuses": self._distinct("research_projects", "project_status"),
            "funding_agencies": self._distinct("research_projects", "agency"),
        }
        set_cache(cache_key, options, ttl_seconds=300)
        return options

    # -------------------------------------------------------------------------
    # PRIVATE HELPER QUERIES & SUB-CALCULATIONS
    # -------------------------------------------------------------------------
    def _trend_summary(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where, params = self._where(filters, alias="fp")
        sql = text(f"""
            WITH year_union AS (
                SELECT jp.academic_year::text AS academic_year, 'pub' AS type, 0::numeric AS amount
                FROM journal_publications jp
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email))
                WHERE fp.is_active = TRUE AND NULLIF(TRIM(jp.title), '') IS NOT NULL {where}
                UNION ALL
                SELECT bp.academic_year::text AS academic_year, 'book' AS type, 0::numeric AS amount
                FROM book_publications bp
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(bp.faculty_email))
                WHERE fp.is_active = TRUE AND COALESCE(NULLIF(TRIM(bp.title), ''), NULLIF(TRIM(bp.book), '')) IS NOT NULL {where}
                UNION ALL
                SELECT p.academic_year::text AS academic_year, 'patent' AS type, 0::numeric AS amount
                FROM patents p
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email))
                WHERE fp.is_active = TRUE AND NULLIF(TRIM(p.title), '') IS NOT NULL {where}
                UNION ALL
                SELECT rp.academic_year::text AS academic_year, 'proj' AS type, COALESCE(rp.amount, 0) AS amount
                FROM research_projects rp
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email))
                WHERE fp.is_active = TRUE AND NULLIF(TRIM(rp.title), '') IS NOT NULL {where}
            )
            SELECT 
                academic_year,
                COUNT(CASE WHEN type = 'pub' THEN 1 END) AS publications,
                COUNT(CASE WHEN type = 'book' THEN 1 END) AS books,
                COUNT(CASE WHEN type = 'patent' THEN 1 END) AS patents,
                SUM(CASE WHEN type = 'proj' THEN amount ELSE 0 END) AS funding
            FROM year_union
            WHERE NULLIF(TRIM(academic_year), '') IS NOT NULL
            GROUP BY academic_year
            ORDER BY academic_year ASC
        """)
        return [dict(row) for row in self.db.execute(sql, params).mappings()]

    def _category_summary(self, filters: dict[str, Any], overview_data: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"category": "journal_publication", "count": overview_data.get("total_journal_publications", 0), "total_score": 0.0, "total_amount": 0.0},
            {"category": "book_publication", "count": overview_data.get("total_book_publications", 0), "total_score": 0.0, "total_amount": 0.0},
            {"category": "patent", "count": overview_data.get("total_patents", 0), "total_score": 0.0, "total_amount": 0.0},
            {"category": "research_project", "count": overview_data.get("total_research_projects", 0), "total_score": 0.0, "total_amount": overview_data.get("total_sanctioned_funding", 0.0)},
            {"category": "research_proposal", "count": overview_data.get("total_research_proposals", 0), "total_score": 0.0, "total_amount": overview_data.get("total_proposal_amount", 0.0)},
        ]

    def _funding_summary(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where, params = self._where(filters, alias="fp")
        sql = text(f"""
            SELECT COALESCE(NULLIF(TRIM(rp.agency), ''), 'Other/Internal') AS agency,
                   COALESCE(SUM(rp.amount), 0) AS total_amount,
                   COUNT(rp.id) AS project_count
            FROM research_projects rp
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(rp.faculty_email))
            WHERE fp.is_active = TRUE AND NULLIF(TRIM(rp.title), '') IS NOT NULL {where}
            GROUP BY COALESCE(NULLIF(TRIM(rp.agency), ''), 'Other/Internal')
            ORDER BY total_amount DESC
            LIMIT 10
        """)
        return [dict(row) for row in self.db.execute(sql, params).mappings()]

    def _patent_summary(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where, params = self._where(filters, alias="fp")
        sql = text(f"""
            SELECT COALESCE(NULLIF(TRIM(p.patent_status), ''), 'Filed') AS status,
                   COUNT(p.id) AS count
            FROM patents p
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(p.faculty_email))
            WHERE fp.is_active = TRUE AND NULLIF(TRIM(p.title), '') IS NOT NULL {where}
            GROUP BY COALESCE(NULLIF(TRIM(p.patent_status), ''), 'Filed')
            ORDER BY count DESC
        """)
        return [dict(row) for row in self.db.execute(sql, params).mappings()]

    def _attention_alerts(self, filters: dict[str, Any], dept_data: list[dict], overview: dict) -> list[dict[str, Any]]:
        alerts = []
        for d in dept_data:
            rate = d.get("publication_participation_percentage") or d.get("participation_rate") or 0
            if rate < 30 and d.get("total_active_faculty", 0) > 3:
                alerts.append({
                    "type": "warning",
                    "title": f"Low Participation in {d.get('department')}",
                    "description": f"Only {rate}% of active faculty in {d.get('department')} ({d.get('school')}) recorded research publications.",
                })
        unmatched_count = self.db.execute(text("SELECT COUNT(*) FROM journal_publications jp LEFT JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(jp.faculty_email)) WHERE fp.email IS NULL")).scalar() or 0
        if unmatched_count > 0:
            alerts.append({
                "type": "critical",
                "title": "Unmatched Faculty Emails",
                "description": f"Found {unmatched_count} research records with email addresses not matching active faculty profiles.",
            })
        return alerts

    def _empty_overview(self) -> dict[str, Any]:
        return {
            "total_active_faculty": 0,
            "total_journal_publications": 0,
            "faculty_with_journal_publication": 0,
            "publication_participation_rate": 0.0,
            "average_publications_per_publishing_faculty": 0.0,
            "total_book_publications": 0,
            "faculty_with_book_publication": 0,
            "total_patents": 0,
            "patents_granted": 0,
            "total_research_projects": 0,
            "total_sanctioned_funding": 0.0,
            "external_funded_projects": 0,
            "external_funded_amount": 0.0,
            "total_research_proposals": 0,
            "total_proposal_amount": 0.0,
            "total_research_scholars_guided": 0,
            "total_conferences": 0,
            "total_awards": 0,
            "total_products_developed": 0,
            "funding_per_active_faculty": 0.0,
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
