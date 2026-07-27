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


def clean_filter(value: Optional[str]) -> Optional[str]:
    """Server-side filter sanitizer to ensure default 'All ...' filters map to None (unfiltered)."""
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    val_lower = val_str.lower()
    if val_lower in {
        "all", "none", "null", "undefined", "",
        "all schools", "all departments", "all years",
        "all designations", "all categories", "all indexing"
    }:
        return None
    if val_lower.startswith("all "):
        return None
    return val_str


def valid_condition_for_table(table_alias: str, table_name: str) -> str:
    """Backend helper returning table-specific record validity condition."""
    if table_name == "journal_publications":
        return f"NULLIF(TRIM({table_alias}.title), '') IS NOT NULL"
    if table_name == "book_publications":
        return f"COALESCE(NULLIF(TRIM({table_alias}.title), ''), NULLIF(TRIM({table_alias}.book), '')) IS NOT NULL"
    if table_name in ("patents", "ipr_records", "research_projects", "external_research_projects", "research_proposals", "conferences", "awards"):
        return f"NULLIF(TRIM({table_alias}.title), '') IS NOT NULL"
    if table_name == "products_developed":
        return f"NULLIF(TRIM({table_alias}.details), '') IS NOT NULL"
    return "1=1"


class FacultyResearchAnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db
        self._table_columns_cache: dict[str, list[str]] = {}

    def _get_table_columns(self, table: str) -> list[str]:
        """Fetch and cache column names for a table."""
        if table in self._table_columns_cache:
            return self._table_columns_cache[table]
        try:
            sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = :tbl")
            cols = [str(r[0]).lower() for r in self.db.execute(sql, {"tbl": table}).all()]
            self._table_columns_cache[table] = cols
            return cols
        except Exception:
            self.db.rollback()
            return []

    def _has_active_filters(self, filters: dict[str, Any]) -> bool:
        """Check if any row-filtering parameter is specified."""
        filter_keys = ("academic_year", "school", "department", "designation", "faculty_email", "category", "indexing", "status", "agency", "search")
        for k in filter_keys:
            val = clean_filter(filters.get(k))
            if val:
                return True
        return False

    def _where(self, filters: dict[str, Any], alias: str = "fp", activity_alias: Optional[str] = None) -> tuple[str, dict[str, Any]]:
        """Construct WHERE clause splitting faculty vs activity table filter parameters."""
        clauses = []
        params: dict[str, Any] = {}

        # Faculty profile filters
        for key in ("school", "department", "designation"):
            val = clean_filter(filters.get(key))
            if val:
                clauses.append(f"AND {alias}.{key} = :{key}")
                params[key] = val

        if filters.get("faculty_email"):
            email_val = clean_filter(filters["faculty_email"])
            if email_val:
                clauses.append(f"AND LOWER(TRIM({alias}.email)) = LOWER(TRIM(:faculty_email))")
                params["faculty_email"] = email_val

        # Activity table filters
        act = activity_alias or alias
        ay_val = clean_filter(filters.get("academic_year"))
        if ay_val:
            clauses.append(f"AND {act}.academic_year = :academic_year")
            params["academic_year"] = ay_val

        idx_val = clean_filter(filters.get("indexing"))
        if idx_val:
            clauses.append(f"AND {act}.indexing = :indexing")
            params["indexing"] = idx_val

        stat_val = clean_filter(filters.get("status"))
        if stat_val:
            clauses.append(f"AND {act}.patent_status = :status")
            params["status"] = stat_val

        ag_val = clean_filter(filters.get("agency"))
        if ag_val:
            clauses.append(f"AND {act}.agency = :agency")
            params["agency"] = ag_val

        return " ".join(clauses), params

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
                "academic_year": clean_filter(filters.get("academic_year")),
                "school": clean_filter(filters.get("school")),
                "department": clean_filter(filters.get("department")),
                "designation": clean_filter(filters.get("designation")),
                "faculty_email": clean_filter(filters.get("faculty_email")),
                "category": clean_filter(filters.get("category")),
                "indexing": clean_filter(filters.get("indexing")),
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

        set_cache(cache_key, response, ttl_seconds=cache_ttl)
        record_endpoint_timing("/api/v1/analytics/research/dashboard", total_time_ms)
        return response

    # -------------------------------------------------------------------------
    # 2. DETAILED ENDPOINTS & REPOSITORIES (PRE-AGGREGATED PER-TABLE CTEs)
    # -------------------------------------------------------------------------
    def overview(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Overview calculation using pre-aggregated per-table CTEs to eliminate row multiplication."""
        if not self._has_active_filters(filters):
            try:
                mv_row = self.db.execute(text("""
                    SELECT 
                        COUNT(faculty_email) AS total_active_faculty,
                        SUM(total_journals) AS total_journal_publications,
                        COUNT(DISTINCT CASE WHEN total_journals > 0 THEN faculty_email END) AS faculty_with_journal_publication,
                        SUM(total_books) AS total_book_publications,
                        COUNT(DISTINCT CASE WHEN total_books > 0 THEN faculty_email END) AS faculty_with_book_publication,
                        SUM(total_patents) AS total_patents,
                        SUM(patents_granted) AS patents_granted,
                        SUM(total_projects) AS total_research_projects,
                        SUM(total_funding) AS total_sanctioned_funding,
                        SUM(external_projects) AS external_funded_projects,
                        SUM(external_funding) AS external_funded_amount,
                        SUM(total_proposals) AS total_research_proposals,
                        SUM(total_proposal_amount) AS total_proposal_amount,
                        SUM(total_scholars_guided) AS total_research_scholars_guided,
                        SUM(total_conferences) AS total_conferences,
                        SUM(total_awards) AS total_awards,
                        SUM(total_products) AS total_products_developed
                    FROM mv_research_faculty_summary
                """)).mappings().first()
                if mv_row and mv_row["total_active_faculty"]:
                    row = dict(mv_row)
                    total_active = row["total_active_faculty"] or 0
                    publishing = row["faculty_with_journal_publication"] or 0
                    journals = row["total_journal_publications"] or 0
                    funding = float(row["total_sanctioned_funding"] or 0)
                    row["publication_participation_rate"] = round((publishing / total_active) * 100, 2) if total_active else 0
                    row["average_publications_per_publishing_faculty"] = round(journals / publishing, 2) if publishing else 0
                    row["funding_per_active_faculty"] = round(funding / total_active, 2) if total_active else 0
                    return row
            except Exception:
                self.db.rollback()

        where_fp, params = self._where(filters, alias="fp")
        where_t, _ = self._where(filters, alias="fp", activity_alias="t")

        sql = text(f"""
            WITH journal_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_journals
              FROM journal_publications t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "journal_publications")} {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            book_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_books
              FROM book_publications t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "book_publications")} {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            patent_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_patents,
                     COUNT(*) FILTER (WHERE LOWER(COALESCE(t.patent_status, '')) LIKE '%grant%') AS patents_granted
              FROM patents t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "patents")} {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            project_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_projects,
                     SUM(COALESCE(t.amount, 0)) AS total_funding,
                     COUNT(*) FILTER (WHERE t.external_project = TRUE) AS external_projects,
                     SUM(CASE WHEN t.external_project = TRUE THEN COALESCE(t.amount, 0) ELSE 0 END) AS external_funding
              FROM (
                SELECT faculty_email, title, amount, NULL AS academic_year, FALSE AS external_project FROM research_projects
                UNION ALL
                SELECT faculty_email, title, amount, NULL AS academic_year, TRUE AS external_project FROM external_research_projects
              ) t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "research_projects")} {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            proposal_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_proposals,
                     SUM(COALESCE(t.amount, 0)) AS total_proposal_amount
              FROM research_proposals t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "research_proposals")} {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            guidance_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_scholars_guided
              FROM research_guidance t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            conference_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_conferences
              FROM conferences t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "conferences")} {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            award_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_awards
              FROM awards t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "awards")} {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            product_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS total_products
              FROM products_developed t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "products_developed")} {where_t}
              GROUP BY LOWER(TRIM(t.faculty_email))
            )
            SELECT
                COUNT(fp.email) AS total_active_faculty,
                COALESCE(SUM(js.total_journals), 0) AS total_journal_publications,
                COUNT(DISTINCT js.faculty_email) AS faculty_with_journal_publication,
                COALESCE(SUM(bs.total_books), 0) AS total_book_publications,
                COUNT(DISTINCT bs.faculty_email) AS faculty_with_book_publication,
                COALESCE(SUM(ps.total_patents), 0) AS total_patents,
                COALESCE(SUM(ps.patents_granted), 0) AS patents_granted,
                COALESCE(SUM(prs.total_projects), 0) AS total_research_projects,
                COALESCE(SUM(prs.total_funding), 0) AS total_sanctioned_funding,
                COALESCE(SUM(prs.external_projects), 0) AS external_funded_projects,
                COALESCE(SUM(prs.external_funding), 0) AS external_funded_amount,
                COALESCE(SUM(props.total_proposals), 0) AS total_research_proposals,
                COALESCE(SUM(props.total_proposal_amount), 0) AS total_proposal_amount,
                COALESCE(SUM(gs.total_scholars_guided), 0) AS total_research_scholars_guided,
                COALESCE(SUM(cs.total_conferences), 0) AS total_conferences,
                COALESCE(SUM(aws.total_awards), 0) AS total_awards,
                COALESCE(SUM(prods.total_products), 0) AS total_products_developed
            FROM faculty_profiles fp
            LEFT JOIN journal_summary js ON LOWER(TRIM(fp.email)) = js.faculty_email
            LEFT JOIN book_summary bs ON LOWER(TRIM(fp.email)) = bs.faculty_email
            LEFT JOIN patent_summary ps ON LOWER(TRIM(fp.email)) = ps.faculty_email
            LEFT JOIN project_summary prs ON LOWER(TRIM(fp.email)) = prs.faculty_email
            LEFT JOIN proposal_summary props ON LOWER(TRIM(fp.email)) = props.faculty_email
            LEFT JOIN guidance_summary gs ON LOWER(TRIM(fp.email)) = gs.faculty_email
            LEFT JOIN conference_summary cs ON LOWER(TRIM(fp.email)) = cs.faculty_email
            LEFT JOIN award_summary aws ON LOWER(TRIM(fp.email)) = aws.faculty_email
            LEFT JOIN product_summary prods ON LOWER(TRIM(fp.email)) = prods.faculty_email
            WHERE fp.is_active = TRUE {where_fp}
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
        """Department summary with MV acceleration and safe fallback."""
        if not self._has_active_filters(filters):
            try:
                base_mv = "WITH summary AS (SELECT * FROM mv_research_department_summary)"
                return self._paginate(base_mv, "SELECT *, ROUND((research_active_faculty::numeric / NULLIF(total_active_faculty, 0)) * 100, 2) AS publication_participation_percentage FROM summary ORDER BY journal_publications DESC", {}, page, page_size)
            except Exception:
                self.db.rollback()

        where_fp, params = self._where(filters, alias="fp")
        where_t, _ = self._where(filters, alias="fp", activity_alias="t")

        base = f"""
            WITH journal_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS journal_publications
              FROM journal_publications t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "journal_publications")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            book_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS book_publications
              FROM book_publications t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "book_publications")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            patent_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS patents, COUNT(*) FILTER (WHERE LOWER(COALESCE(t.patent_status, '')) LIKE '%grant%') AS patents_granted
              FROM patents t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "patents")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            project_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS research_projects, SUM(COALESCE(t.amount, 0)) AS total_project_funding
              FROM (SELECT faculty_email, title, amount, NULL AS academic_year FROM research_projects UNION ALL SELECT faculty_email, title, amount, NULL AS academic_year FROM external_research_projects) t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "research_projects")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            proposal_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS research_proposals, SUM(COALESCE(t.amount, 0)) AS total_proposal_amount
              FROM research_proposals t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "research_proposals")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            summary AS (
                SELECT
                    COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') AS school,
                    COALESCE(NULLIF(TRIM(fp.department), ''), COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') || ' (No department mapped)') AS department,
                    COUNT(DISTINCT fp.email) FILTER (WHERE fp.is_active = TRUE) AS total_active_faculty,
                    COUNT(DISTINCT js.faculty_email) AS faculty_who_published_papers,
                    COALESCE(SUM(js.journal_publications), 0) AS journal_publications,
                    COALESCE(SUM(bs.book_publications), 0) AS book_publications,
                    COALESCE(SUM(ps.patents), 0) AS patents,
                    COALESCE(SUM(ps.patents_granted), 0) AS patents_granted,
                    COALESCE(SUM(prs.research_projects), 0) AS research_projects,
                    COALESCE(SUM(prs.total_project_funding), 0) AS total_project_funding,
                    COALESCE(SUM(props.research_proposals), 0) AS research_proposals,
                    COALESCE(SUM(props.total_proposal_amount), 0) AS total_proposal_amount
                FROM faculty_profiles fp
                LEFT JOIN journal_summary js ON LOWER(TRIM(fp.email)) = js.faculty_email
                LEFT JOIN book_summary bs ON LOWER(TRIM(fp.email)) = bs.faculty_email
                LEFT JOIN patent_summary ps ON LOWER(TRIM(fp.email)) = ps.faculty_email
                LEFT JOIN project_summary prs ON LOWER(TRIM(fp.email)) = prs.faculty_email
                LEFT JOIN proposal_summary props ON LOWER(TRIM(fp.email)) = props.faculty_email
                WHERE fp.is_active = TRUE {where_fp}
                GROUP BY COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned'), COALESCE(NULLIF(TRIM(fp.department), ''), COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') || ' (No department mapped)')
            )
        """
        return self._paginate(base, "SELECT *, ROUND((faculty_who_published_papers::numeric / NULLIF(total_active_faculty, 0)) * 100, 2) AS publication_participation_percentage FROM summary ORDER BY journal_publications DESC", params, page, page_size)

    def schools(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        """School summary with MV acceleration."""
        if not self._has_active_filters(filters):
            try:
                base_mv = "WITH summary AS (SELECT * FROM mv_research_school_summary)"
                return self._paginate(base_mv, "SELECT * FROM summary ORDER BY journal_publications DESC", {}, page, page_size)
            except Exception:
                self.db.rollback()

        where_fp, params = self._where(filters, alias="fp")
        where_t, _ = self._where(filters, alias="fp", activity_alias="t")

        base = f"""
            WITH journal_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS journal_publications
              FROM journal_publications t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "journal_publications")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            book_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS book_publications
              FROM book_publications t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "book_publications")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            patent_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS patents
              FROM patents t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "patents")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            project_summary AS (
              SELECT LOWER(TRIM(t.faculty_email)) AS faculty_email, COUNT(*) AS research_projects, SUM(COALESCE(t.amount, 0)) AS total_project_funding
              FROM (SELECT faculty_email, title, amount, NULL AS academic_year FROM research_projects UNION ALL SELECT faculty_email, title, amount, NULL AS academic_year FROM external_research_projects) t
              JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
              WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "research_projects")} {where_t} GROUP BY LOWER(TRIM(t.faculty_email))
            ),
            summary AS (
                SELECT
                    COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') AS school,
                    COUNT(DISTINCT fp.email) FILTER (WHERE fp.is_active = TRUE) AS total_active_faculty,
                    COUNT(DISTINCT js.faculty_email) AS faculty_who_published_papers,
                    COALESCE(SUM(js.journal_publications), 0) AS journal_publications,
                    COALESCE(SUM(bs.book_publications), 0) AS book_publications,
                    COALESCE(SUM(ps.patents), 0) AS patents,
                    COALESCE(SUM(prs.research_projects), 0) AS research_projects,
                    COALESCE(SUM(prs.total_project_funding), 0) AS total_project_funding
                FROM faculty_profiles fp
                LEFT JOIN journal_summary js ON LOWER(TRIM(fp.email)) = js.faculty_email
                LEFT JOIN book_summary bs ON LOWER(TRIM(fp.email)) = bs.faculty_email
                LEFT JOIN patent_summary ps ON LOWER(TRIM(fp.email)) = ps.faculty_email
                LEFT JOIN project_summary prs ON LOWER(TRIM(fp.email)) = prs.faculty_email
                WHERE fp.is_active = TRUE {where_fp}
                GROUP BY COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned')
            )
        """
        return self._paginate(base, "SELECT *, ROUND((faculty_who_published_papers::numeric / NULLIF(total_active_faculty, 0)) * 100, 2) AS participation_rate FROM summary ORDER BY journal_publications DESC", params, page, page_size)

    def faculty(self, filters: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        """Faculty records summary."""
        where_fp, params = self._where(filters, alias="fp")
        sql = f"""
            WITH activity AS (
                SELECT fp.email AS faculty_email, fp.employee_id, fp.full_name,
                       COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') AS school,
                       COALESCE(NULLIF(TRIM(fp.department), ''), COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') || ' (No department mapped)') AS department,
                       fp.designation,
                       COUNT(DISTINCT jp.id) FILTER (WHERE {valid_condition_for_table("jp", "journal_publications")}) AS journal_publications,
                       COUNT(DISTINCT bp.id) FILTER (WHERE {valid_condition_for_table("bp", "book_publications")}) AS book_publications,
                       COUNT(DISTINCT p.id) FILTER (WHERE {valid_condition_for_table("p", "patents")}) AS patents,
                       COUNT(DISTINCT rp.id) FILTER (WHERE {valid_condition_for_table("rp", "research_projects")}) AS research_projects,
                       COALESCE(SUM(DISTINCT rp.amount), 0) AS project_funding,
                       COUNT(DISTINCT rpr.id) FILTER (WHERE {valid_condition_for_table("rpr", "research_proposals")}) AS proposals,
                       COUNT(DISTINCT rg.id) AS research_guidance,
                       COUNT(DISTINCT c.id) FILTER (WHERE {valid_condition_for_table("c", "conferences")}) AS conferences,
                       COUNT(DISTINCT a.id) FILTER (WHERE {valid_condition_for_table("a", "awards")}) AS awards,
                       COUNT(DISTINCT pd.id) FILTER (WHERE {valid_condition_for_table("pd", "products_developed")}) AS products_developed,
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
                WHERE fp.is_active = TRUE {where_fp}
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
        """Paginated records for specific research category with pre-pagination summary calculation."""
        try:
            tbl_cols = self._get_table_columns(table)
            where, params = self._where(filters, alias="fp", activity_alias="t")
            params["limit"] = page_size
            params["offset"] = (page - 1) * page_size

            sort_by_param = (filters.get("sort_by") or "").strip().lower()
            sort_col = "id"
            if sort_by_param and sort_by_param in tbl_cols:
                sort_col = sort_by_param
            else:
                for candidate in ("academic_year", "publication_year", "year", "created_at", "id"):
                    if candidate in tbl_cols:
                        sort_col = candidate
                        break

            sort_order = "DESC" if (filters.get("sort_order") or "desc").lower() == "desc" else "ASC"
            valid_clause = valid_condition_for_table("t", table)

            search_clause = ""
            if filters.get("search"):
                text_search_targets = []
                for candidate in ("title", "paper_title", "book", "book_title", "details", "journal_name", "scholar_name", "project_title", "award_name"):
                    if candidate in tbl_cols:
                        text_search_targets.append(f"LOWER(t.{candidate}::text) LIKE :search")
                
                search_targets_str = " OR ".join(text_search_targets)
                if search_targets_str:
                    search_clause = f" AND (LOWER(fp.full_name) LIKE :search OR {search_targets_str}) "
                else:
                    search_clause = " AND LOWER(fp.full_name) LIKE :search "
                params["search"] = f"%{filters['search'].lower()}%"

            # 1. Unpaginated total count
            count_sql = text(f"""
                SELECT COUNT(*) FROM {table} t
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                WHERE fp.is_active = TRUE AND {valid_clause} {where} {search_clause}
            """)
            total = int(self.db.execute(count_sql, params).scalar() or 0)

            # 2. Paginated items
            sql = text(f"""
                SELECT t.*, fp.full_name, fp.employee_id,
                       COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') AS school,
                       COALESCE(NULLIF(TRIM(fp.department), ''), COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') || ' (No department mapped)') AS department,
                       fp.designation
                FROM {table} t
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                WHERE fp.is_active = TRUE AND {valid_clause} {where} {search_clause}
                ORDER BY t.{sort_col} {sort_order}
                LIMIT :limit OFFSET :offset
            """)
            rows = self.db.execute(sql, params).mappings()
            items = [dict(row) for row in rows]

            # 3. Calculate category summary BEFORE pagination
            summary = self._calculate_table_summary(table, filters, total)

            return {
                "items": items,
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": ceil(total / page_size) if total else 0,
                "summary": summary,
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error fetching category_records for table {table}: {e}")
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
                "total_pages": 0,
                "summary": {},
            }

    def _calculate_table_summary(self, table: str, filters: dict[str, Any], total: int) -> dict[str, Any]:
        """Calculate unpaginated summary metrics before applying offset and limit pagination."""
        try:
            where, params = self._where(filters, alias="fp", activity_alias="t")
            if table == "patents":
                sql = text(f"""
                    SELECT 
                        COUNT(t.id) AS total_valid_patents,
                        COUNT(DISTINCT LOWER(TRIM(t.faculty_email))) AS patent_filing_faculty,
                        COUNT(t.id) FILTER (WHERE LOWER(COALESCE(t.patent_status, '')) LIKE '%grant%') AS patents_granted
                    FROM patents t
                    JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                    WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "patents")} {where}
                """)
                row = dict(self.db.execute(sql, params).mappings().one())
                tot = row["total_valid_patents"] or 0
                granted = row["patents_granted"] or 0
                pending = tot - granted
                rate = round((granted / tot) * 100, 2) if tot > 0 else 0.0

                ipr_count = 0
                try:
                    ipr_sql = text(f"""
                        SELECT COUNT(t.id)
                        FROM ipr_records t
                        JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                        WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "ipr_records")} {where}
                    """)
                    ipr_count = int(self.db.execute(ipr_sql, params).scalar() or 0)
                except Exception:
                    self.db.rollback()

                return {
                    "total_valid_patents": tot,
                    "patent_filing_faculty": row["patent_filing_faculty"] or 0,
                    "patents_granted": granted,
                    "patents_pending": pending,
                    "patent_grant_rate": rate,
                    "total_ipr_records": ipr_count,
                }
            elif table == "journal_publications":
                return {
                    "total_journal_publications": total,
                    "publishing_faculty": self._count_distinct_faculty("journal_publications", filters),
                }
            elif table == "book_publications":
                return {
                    "total_book_publications": total,
                    "book_publishing_faculty": self._count_distinct_faculty("book_publications", filters),
                }
            elif table == "research_projects":
                sql = text(f"""
                    SELECT COALESCE(SUM(t.amount), 0)
                    FROM (
                        SELECT faculty_email, title, amount, NULL AS academic_year FROM research_projects
                        UNION ALL
                        SELECT faculty_email, title, amount, NULL AS academic_year FROM external_research_projects
                    ) t
                    JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                    WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "research_projects")} {where}
                """)
                funding = float(self.db.execute(sql, params).scalar() or 0.0)
                return {
                    "total_research_projects": total,
                    "total_sanctioned_funding": funding,
                }
            elif table == "research_guidance":
                return {
                    "total_scholars_guided": total,
                    "guiding_faculty": self._count_distinct_faculty("research_guidance", filters),
                }
        except Exception as e:
            self.db.rollback()
            logger.error("Error calculating summary for table %s: %s", table, e)
        return {"total": total}

    def _count_distinct_faculty(self, table: str, filters: dict[str, Any]) -> int:
        try:
            where, params = self._where(filters, alias="fp", activity_alias="t")
            valid_clause = valid_condition_for_table("t", table)
            sql = text(f"""
                SELECT COUNT(DISTINCT LOWER(TRIM(t.faculty_email)))
                FROM {table} t
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                WHERE fp.is_active = TRUE AND {valid_clause} {where}
            """)
            return int(self.db.execute(sql, params).scalar() or 0)
        except Exception:
            self.db.rollback()
            return 0

    def debug_counts(self, metric: str = "patents") -> dict[str, Any]:
        """Debug endpoint to verify consistency between All Schools total, dashboard total, and individual school counts."""
        table_map = {
            "patents": ("patents", "title"),
            "journals": ("journal_publications", "title"),
            "books": ("book_publications", "title"),
            "projects": ("research_projects", "title"),
        }
        table, title_col = table_map.get(metric.lower(), ("patents", "title"))

        # 1. All Schools Total (Unfiltered)
        sql_all = text(f"""
            SELECT COUNT(t.id)
            FROM {table} t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", table)}
        """)
        all_schools_total = int(self.db.execute(sql_all).scalar() or 0)

        # 2. By School Breakdown
        sql_by_school = text(f"""
            SELECT COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned') AS school, COUNT(t.id) AS total
            FROM {table} t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", table)}
            GROUP BY COALESCE(NULLIF(TRIM(fp.school), ''), 'Unassigned')
            ORDER BY total DESC
        """)
        rows = self.db.execute(sql_by_school).mappings().all()
        by_school = [{"school": row["school"], "total": row["total"]} for row in rows]
        sum_of_schools = sum(item["total"] for item in by_school)

        max_single_school = max([item["total"] for item in by_school], default=0)
        is_consistent = all_schools_total >= max_single_school

        # 3. Dashboard Total Comparison
        dash = self.dashboard_summary({}, refresh=True)
        dash_metric_key = f"total_{metric}" if metric != "journals" else "total_journal_publications"
        dash_total = dash.get("overview", {}).get(dash_metric_key, 0)
        if metric == "patents":
            dash_total = dash.get("overview", {}).get("total_patents", 0)
        elif metric == "books":
            dash_total = dash.get("overview", {}).get("total_book_publications", 0)
        elif metric == "projects":
            dash_total = dash.get("overview", {}).get("total_research_projects", 0)

        # 4. Detail Summary Total Comparison
        detail_res = self.category_records(table, {}, 1, 10)
        detail_summary_total = detail_res.get("total", 0)

        return {
            "metric": metric,
            "all_schools_total": all_schools_total,
            "by_school": by_school,
            "sum_of_schools": sum_of_schools,
            "max_single_school": max_single_school,
            "is_consistent": is_consistent,
            "dashboard_total": dash_total,
            "detail_summary_total": detail_summary_total,
            "dashboard_matches_detail": (dash_total == detail_summary_total),
        }

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
        """Available filter options cached for 300s with MV acceleration."""
        cache_key = "analytics:filter_options"
        is_hit, cached_val = get_cache(cache_key)
        if is_hit and cached_val:
            return cached_val

        try:
            mv_options = self.db.execute(text("""
                SELECT 
                    academic_years,
                    schools,
                    departments,
                    designations,
                    indexing_options AS indexing
                FROM mv_research_filter_options
            """)).mappings().first()
            if mv_options:
                options = {
                    "academic_years": list(mv_options["academic_years"] or []),
                    "schools": list(mv_options["schools"] or []),
                    "departments": list(mv_options["departments"] or []),
                    "designations": list(mv_options["designations"] or []),
                    "indexing": list(mv_options["indexing"] or []),
                    "patent_statuses": self._distinct("patents", "patent_status"),
                    "project_statuses": self._distinct("research_projects", "project_status"),
                    "funding_agencies": self._distinct("research_projects", "agency"),
                }
                set_cache(cache_key, options, ttl_seconds=300)
                return options
        except Exception:
            self.db.rollback()

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
        if not self._has_active_filters(filters):
            try:
                mv_rows = self.db.execute(text("SELECT * FROM mv_research_yearly_trend ORDER BY academic_year ASC")).mappings().all()
                if mv_rows:
                    return [dict(row) for row in mv_rows]
            except Exception:
                self.db.rollback()

        where_t, params = self._where(filters, alias="fp", activity_alias="t")
        sql = text(f"""
            WITH year_union AS (
                SELECT t.academic_year::text AS academic_year, 'pub' AS type, 0::numeric AS amount
                FROM journal_publications t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "journal_publications")} {where_t}
                UNION ALL
                SELECT t.academic_year::text AS academic_year, 'book' AS type, 0::numeric AS amount
                FROM book_publications t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "book_publications")} {where_t}
                UNION ALL
                SELECT t.academic_year::text AS academic_year, 'patent' AS type, 0::numeric AS amount
                FROM patents t JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "patents")} {where_t}
                UNION ALL
                SELECT t.academic_year::text AS academic_year, 'proj' AS type, COALESCE(t.amount, 0) AS amount
                FROM (SELECT faculty_email, title, amount, NULL AS academic_year FROM research_projects UNION ALL SELECT faculty_email, title, amount, NULL AS academic_year FROM external_research_projects) t
                JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
                WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "research_projects")} {where_t}
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
        where_t, params = self._where(filters, alias="fp", activity_alias="t")
        sql = text(f"""
            SELECT COALESCE(NULLIF(TRIM(t.agency), ''), 'Other/Internal') AS agency,
                   COALESCE(SUM(t.amount), 0) AS total_amount,
                   COUNT(t.id) AS project_count
            FROM (SELECT id, faculty_email, title, amount, agency, NULL AS academic_year FROM research_projects UNION ALL SELECT id, faculty_email, title, amount, agency, NULL AS academic_year FROM external_research_projects) t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "research_projects")} {where_t}
            GROUP BY COALESCE(NULLIF(TRIM(t.agency), ''), 'Other/Internal')
            ORDER BY total_amount DESC
            LIMIT 10
        """)
        return [dict(row) for row in self.db.execute(sql, params).mappings()]

    def _patent_summary(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where_t, params = self._where(filters, alias="fp", activity_alias="t")
        sql = text(f"""
            SELECT COALESCE(NULLIF(TRIM(t.patent_status), ''), 'Filed') AS status,
                   COUNT(t.id) AS count
            FROM patents t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", "patents")} {where_t}
            GROUP BY COALESCE(NULLIF(TRIM(t.patent_status), ''), 'Filed')
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
        where_t, params = self._where(filters, alias="fp", activity_alias="t")
        sql = text(f"""
            SELECT t.*
            FROM {table} t
            JOIN faculty_profiles fp ON LOWER(TRIM(fp.email)) = LOWER(TRIM(t.faculty_email))
            WHERE fp.is_active = TRUE AND {valid_condition_for_table("t", table)} {where_t}
            ORDER BY t.academic_year DESC
            LIMIT 200
        """)
        return [dict(row) for row in self.db.execute(sql, params).mappings()]

    def _paginate(self, with_sql: str, select_sql: str, params: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
        params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
        count = int(self.db.execute(text(f"{with_sql} SELECT COUNT(*) FROM ({select_sql}) counted"), params).scalar() or 0)
        rows = self.db.execute(text(f"{with_sql} {select_sql} LIMIT :limit OFFSET :offset"), params).mappings()
        return {"items": [dict(row) for row in rows], "page": page, "page_size": page_size, "total": count, "total_pages": ceil(count / page_size) if count else 0}

    def _distinct(self, table: str, column: str) -> list[Any]:
        try:
            sql = text(f"SELECT DISTINCT {column} FROM {table} WHERE NULLIF(TRIM({column}::text), '') IS NOT NULL ORDER BY {column}")
            return [row[0] for row in self.db.execute(sql).all()]
        except Exception:
            self.db.rollback()
            return []
