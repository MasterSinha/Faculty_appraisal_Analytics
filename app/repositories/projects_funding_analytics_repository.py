import datetime
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import Table, and_, case, distinct, func, or_, select, text
from sqlalchemy.orm import Session

from app.core.constants import (
    AGENCY_COLUMNS,
    AMOUNT_COLUMNS,
    DEPARTMENT_COLUMNS,
    EMAIL_COLUMNS,
    EMPLOYEE_COLUMNS,
    NAME_COLUMNS,
    PROJECT_TYPE_COLUMNS,
    SCHOOL_COLUMNS,
    STATUS_COLUMNS,
    TITLE_COLUMNS,
    YEAR_COLUMNS,
)
from app.models.schema_reflector import SchemaReflector


def is_valid_filter(val: Any) -> bool:
    if val is None:
        return False
    s = str(val).strip().lower()
    if s in ("", "all", "all schools", "all departments", "all designations", "all categories", "all years", "all indexing", "none", "null"):
        return False
    return True


def normalize_status(raw_status: Optional[str]) -> str:
    if not raw_status or not str(raw_status).strip():
        return "Unknown"
    s = str(raw_status).strip().lower()
    if "sanc" in s or "approve" in s or "grant" in s or "award" in s:
        return "Sanctioned"
    if "ongoi" in s or "in progress" in s or "active" in s or "current" in s:
        return "Ongoing"
    if "complet" in s or "finish" in s or "done" in s:
        return "Completed"
    if "submit" in s:
        return "Submitted"
    if "propos" in s:
        return "Proposed"
    if "reject" in s or "refus" in s or "declin" in s:
        return "Rejected"
    if "close" in s or "terminat" in s:
        return "Closed"
    return "Unknown"


def normalize_role(raw_role: Optional[str]) -> str:
    if not raw_role or not str(raw_role).strip():
        return "Other"
    r = str(raw_role).strip().lower()
    if "co-pi" in r or "co pi" in r or "co-principal" in r or "coprincipal" in r:
        return "Co-Principal Investigator"
    if "principal" in r or r == "pi" or "project leader" in r or "lead investigator" in r:
        return "Principal Investigator"
    if "co-i" in r or "co i" in r or "co-investigator" in r or "coinvestigator" in r:
        return "Co-Investigator"
    if "member" in r or "team" in r or "researcher" in r or "fellow" in r:
        return "Team Member"
    return "Other"


def parse_numeric_year(val: Any) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.year
    s = str(val).strip()
    match = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if match:
        return int(match.group(1))
    return None


class ProjectsFundingAnalyticsRepository:
    """Repository for Projects and Funding Analytics using SQLAlchemy Core."""

    def __init__(self, db: Session):
        self.db = db
        self.reflector = SchemaReflector(db)

    def _logical_table(self, candidates: List[str]) -> Optional[Table]:
        name = self.reflector.resolve_table_name(candidates)
        if not name:
            return None
        try:
            return self.reflector.get_table(name)
        except Exception:
            return None

    def _get_tables(self) -> Tuple[Optional[Table], Optional[Table], Optional[Table], Optional[Table]]:
        internal_proj_table = self._logical_table(["research_projects", "internal_research_projects", "projects", "faculty_research_projects"])
        external_proj_table = self._logical_table(["external_research_projects", "external_projects", "sponsored_projects"])
        proposals_table = self._logical_table(["research_proposals", "proposals", "grant_proposals"])
        faculty_table = self._logical_table(["faculty_profiles", "faculty", "users"])
        return internal_proj_table, external_proj_table, proposals_table, faculty_table

    def _get_active_faculty_profiles(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        _, _, _, faculty_table = self._get_tables()
        if faculty_table is None:
            return []

        f_cols = SchemaReflector.column_names(faculty_table)
        f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
        f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
        f_emp = SchemaReflector.first_existing(f_cols, EMPLOYEE_COLUMNS) or "employee_id"
        f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
        f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"
        f_desig = SchemaReflector.first_existing(f_cols, ["designation", "role"]) or "designation"

        select_fields = [
            faculty_table.c[f_email].label("email"),
            faculty_table.c[f_name].label("faculty_name") if f_name in faculty_table.c else text("''").label("faculty_name"),
            faculty_table.c[f_emp].label("employee_id") if f_emp in faculty_table.c else text("''").label("employee_id"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else text("''").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else text("''").label("school"),
            faculty_table.c[f_desig].label("designation") if f_desig in faculty_table.c else text("''").label("designation"),
        ]

        if "is_active" in faculty_table.c:
            select_fields.append(faculty_table.c.is_active.label("is_active"))
        else:
            select_fields.append(text("1").label("is_active"))

        stmt = select(*select_fields)
        clauses = []
        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        if is_valid_filter(filters.get("school")) and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])
        if is_valid_filter(filters.get("department")) and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])
        if is_valid_filter(filters.get("designation")) and f_desig in faculty_table.c:
            clauses.append(faculty_table.c[f_desig] == filters["designation"])
        if filters.get("faculty_email"):
            clauses.append(func.lower(func.trim(faculty_table.c[f_email])) == str(filters["faculty_email"]).lower().strip())

        if clauses:
            stmt = stmt.where(and_(*clauses))

        res = self.db.execute(stmt).fetchall()
        profiles = []
        for r in res:
            p = dict(r._mapping)
            p["email"] = str(p.get("email") or "").lower().strip()
            p["is_active"] = bool(p.get("is_active"))
            profiles.append(p)
        return profiles

    def _get_filtered_projects(self, target_table: Optional[Table], is_external: bool, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        _, _, _, faculty_table = self._get_tables()
        if target_table is None or faculty_table is None:
            return []

        p_cols = SchemaReflector.column_names(target_table)
        f_cols = SchemaReflector.column_names(faculty_table)

        p_id = SchemaReflector.first_existing(p_cols, ["id", "project_id"]) or "id"
        p_email = SchemaReflector.first_existing(p_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        p_title = SchemaReflector.first_existing(p_cols, TITLE_COLUMNS) or "title"
        p_agency = SchemaReflector.first_existing(p_cols, AGENCY_COLUMNS) or "agency"
        p_date = SchemaReflector.first_existing(p_cols, ["sanction_date", "date", "start_date"]) or "sanction_date"
        p_amount = SchemaReflector.first_existing(p_cols, AMOUNT_COLUMNS) or "amount"
        p_role = SchemaReflector.first_existing(p_cols, ["role", "investigator_role"]) or "role"
        p_status = SchemaReflector.first_existing(p_cols, STATUS_COLUMNS) or "project_status"
        p_year = SchemaReflector.first_existing(p_cols, YEAR_COLUMNS) or "academic_year"
        p_score = SchemaReflector.first_existing(p_cols, ["score", "self_score"]) or "score"
        p_hod = SchemaReflector.first_existing(p_cols, ["hod_score"]) or "hod_score"
        p_dir = SchemaReflector.first_existing(p_cols, ["director_score"]) or "director_score"
        p_dean = SchemaReflector.first_existing(p_cols, ["dean_score"]) or "dean_score"
        p_vc = SchemaReflector.first_existing(p_cols, ["vc_score", "vc_approved_score", "final_score"]) or "vc_score"

        f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
        f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
        f_emp = SchemaReflector.first_existing(f_cols, EMPLOYEE_COLUMNS) or "employee_id"
        f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
        f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"
        f_desig = SchemaReflector.first_existing(f_cols, ["designation", "role"]) or "designation"

        select_fields = [
            target_table.c[p_id].label("id") if p_id in target_table.c else target_table.c[p_cols[0]].label("id"),
            target_table.c[p_email].label("p_faculty_email") if p_email in target_table.c else text("''").label("p_faculty_email"),
            target_table.c[p_title].label("title") if p_title in target_table.c else text("''").label("title"),
            target_table.c[p_agency].label("agency") if p_agency in target_table.c else text("''").label("agency"),
            target_table.c[p_date].label("sanction_date") if p_date in target_table.c else text("NULL").label("sanction_date"),
            target_table.c[p_amount].label("amount") if p_amount in target_table.c else text("0.0").label("amount"),
            target_table.c[p_role].label("role") if p_role in target_table.c else text("''").label("role"),
            target_table.c[p_status].label("project_status") if p_status in target_table.c else text("''").label("project_status"),
            target_table.c[p_year].label("academic_year") if p_year in target_table.c else text("''").label("academic_year"),
            target_table.c[p_score].label("score") if p_score in target_table.c else text("0.0").label("score"),
            target_table.c[p_hod].label("hod_score") if p_hod in target_table.c else text("0.0").label("hod_score"),
            target_table.c[p_dir].label("director_score") if p_dir in target_table.c else text("0.0").label("director_score"),
            target_table.c[p_dean].label("dean_score") if p_dean in target_table.c else text("0.0").label("dean_score"),
            target_table.c[p_vc].label("vc_score") if p_vc in target_table.c else text("0.0").label("vc_score"),
            faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else text("''").label("f_email"),
            faculty_table.c[f_name].label("faculty_name") if f_name in faculty_table.c else text("''").label("faculty_name"),
            faculty_table.c[f_emp].label("employee_id") if f_emp in faculty_table.c else text("''").label("employee_id"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else text("''").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else text("''").label("school"),
            faculty_table.c[f_desig].label("designation") if f_desig in faculty_table.c else text("''").label("designation"),
        ]

        stmt = select(*select_fields)
        p_email_col = target_table.c[p_email] if p_email in target_table.c else target_table.c[p_cols[0]]
        f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]

        join_clause = func.lower(func.trim(p_email_col)) == func.lower(func.trim(f_email_col))
        stmt = stmt.select_from(target_table.outerjoin(faculty_table, join_clause))

        clauses = []
        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        # VALID PROJECT CONDITION: title IS NOT NULL AND TRIM(title) <> ''
        p_title_col = target_table.c[p_title] if p_title in target_table.c else target_table.c[p_cols[0]]
        clauses.append(p_title_col.isnot(None))
        clauses.append(func.trim(p_title_col) != "")

        if is_valid_filter(filters.get("academic_year")) and p_year in target_table.c:
            clauses.append(func.cast(target_table.c[p_year], text("VARCHAR")) == str(filters["academic_year"]))

        if is_valid_filter(filters.get("school")) and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])

        if is_valid_filter(filters.get("department")) and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])

        if is_valid_filter(filters.get("designation")) and f_desig in faculty_table.c:
            clauses.append(faculty_table.c[f_desig] == filters["designation"])

        if filters.get("faculty_email"):
            target_email = str(filters["faculty_email"]).lower().strip()
            clauses.append(func.lower(func.trim(f_email_col)) == target_email)

        if filters.get("agency") and p_agency in target_table.c:
            target_agency = f"%{str(filters['agency']).lower().strip()}%"
            clauses.append(func.lower(func.trim(target_table.c[p_agency])).like(target_agency))

        if filters.get("search"):
            search_term = f"%{str(filters['search']).lower().strip()}%"
            search_clauses = [
                func.lower(p_title_col).like(search_term),
                func.lower(f_email_col).like(search_term),
            ]
            if p_agency in target_table.c:
                search_clauses.append(func.lower(target_table.c[p_agency]).like(search_term))
            if f_name in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_name]).like(search_term))
            clauses.append(or_(*search_clauses))

        if clauses:
            stmt = stmt.where(and_(*clauses))

        result = self.db.execute(stmt).fetchall()
        rows = []
        for r in result:
            rd = dict(r._mapping)
            rd["faculty_email"] = str(rd.get("f_email") or rd.get("p_faculty_email") or "").lower().strip()
            rd["normalized_status"] = normalize_status(rd.get("project_status"))
            rd["normalized_role"] = normalize_role(rd.get("role"))
            rd["is_external"] = is_external

            if filters.get("project_status") and rd["normalized_status"].lower() != str(filters["project_status"]).lower().strip():
                continue
            if filters.get("role") and rd["normalized_role"].lower() != str(filters["role"]).lower().strip():
                continue

            rd["amount"] = float(rd.get("amount") or 0.0)

            vc = float(rd.get("vc_score") or 0.0)
            dn = float(rd.get("dean_score") or 0.0)
            dr = float(rd.get("director_score") or 0.0)
            hd = float(rd.get("hod_score") or 0.0)
            sc = float(rd.get("score") or 0.0)
            final_score = vc if vc > 0 else (dn if dn > 0 else (dr if dr > 0 else (hd if hd > 0 else sc)))
            rd["final_validated_score"] = float(final_score)

            rows.append(rd)
        return rows

    def _get_filtered_proposals(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        _, _, proposals_table, faculty_table = self._get_tables()
        if proposals_table is None or faculty_table is None:
            return []

        pr_cols = SchemaReflector.column_names(proposals_table)
        f_cols = SchemaReflector.column_names(faculty_table)

        pr_id = SchemaReflector.first_existing(pr_cols, ["id", "proposal_id"]) or "id"
        pr_email = SchemaReflector.first_existing(pr_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        pr_title = SchemaReflector.first_existing(pr_cols, TITLE_COLUMNS) or "title"
        pr_agency = SchemaReflector.first_existing(pr_cols, AGENCY_COLUMNS) or "agency"
        pr_dur = SchemaReflector.first_existing(pr_cols, ["duration", "project_duration"]) or "duration"
        pr_amount = SchemaReflector.first_existing(pr_cols, AMOUNT_COLUMNS) or "amount"
        pr_year = SchemaReflector.first_existing(pr_cols, YEAR_COLUMNS) or "academic_year"
        pr_score = SchemaReflector.first_existing(pr_cols, ["score", "self_score"]) or "score"

        f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
        f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
        f_emp = SchemaReflector.first_existing(f_cols, EMPLOYEE_COLUMNS) or "employee_id"
        f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
        f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"
        f_desig = SchemaReflector.first_existing(f_cols, ["designation", "role"]) or "designation"

        select_fields = [
            proposals_table.c[pr_id].label("id") if pr_id in proposals_table.c else proposals_table.c[pr_cols[0]].label("id"),
            proposals_table.c[pr_email].label("pr_faculty_email") if pr_email in proposals_table.c else text("''").label("pr_faculty_email"),
            proposals_table.c[pr_title].label("title") if pr_title in proposals_table.c else text("''").label("title"),
            proposals_table.c[pr_agency].label("agency") if pr_agency in proposals_table.c else text("''").label("agency"),
            proposals_table.c[pr_dur].label("duration") if pr_dur in proposals_table.c else text("''").label("duration"),
            proposals_table.c[pr_amount].label("amount") if pr_amount in proposals_table.c else text("0.0").label("amount"),
            proposals_table.c[pr_year].label("academic_year") if pr_year in proposals_table.c else text("''").label("academic_year"),
            proposals_table.c[pr_score].label("score") if pr_score in proposals_table.c else text("0.0").label("score"),
            faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else text("''").label("f_email"),
            faculty_table.c[f_name].label("faculty_name") if f_name in faculty_table.c else text("''").label("faculty_name"),
            faculty_table.c[f_emp].label("employee_id") if f_emp in faculty_table.c else text("''").label("employee_id"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else text("''").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else text("''").label("school"),
            faculty_table.c[f_desig].label("designation") if f_desig in faculty_table.c else text("''").label("designation"),
        ]

        stmt = select(*select_fields)
        pr_email_col = proposals_table.c[pr_email] if pr_email in proposals_table.c else proposals_table.c[pr_cols[0]]
        f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]

        join_clause = func.lower(func.trim(pr_email_col)) == func.lower(func.trim(f_email_col))
        stmt = stmt.select_from(proposals_table.outerjoin(faculty_table, join_clause))

        clauses = []
        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        # VALID PROPOSAL CONDITION: title IS NOT NULL AND TRIM(title) <> ''
        pr_title_col = proposals_table.c[pr_title] if pr_title in proposals_table.c else proposals_table.c[pr_cols[0]]
        clauses.append(pr_title_col.isnot(None))
        clauses.append(func.trim(pr_title_col) != "")

        if is_valid_filter(filters.get("academic_year")) and pr_year in proposals_table.c:
            clauses.append(func.cast(proposals_table.c[pr_year], text("VARCHAR")) == str(filters["academic_year"]))

        if is_valid_filter(filters.get("school")) and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])

        if is_valid_filter(filters.get("department")) and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])

        if is_valid_filter(filters.get("designation")) and f_desig in faculty_table.c:
            clauses.append(faculty_table.c[f_desig] == filters["designation"])

        if filters.get("faculty_email"):
            target_email = str(filters["faculty_email"]).lower().strip()
            clauses.append(func.lower(func.trim(f_email_col)) == target_email)

        if filters.get("agency") and pr_agency in proposals_table.c:
            target_agency = f"%{str(filters['agency']).lower().strip()}%"
            clauses.append(func.lower(func.trim(proposals_table.c[pr_agency])).like(target_agency))

        if filters.get("search"):
            search_term = f"%{str(filters['search']).lower().strip()}%"
            search_clauses = [
                func.lower(pr_title_col).like(search_term),
                func.lower(f_email_col).like(search_term),
            ]
            if pr_agency in proposals_table.c:
                search_clauses.append(func.lower(proposals_table.c[pr_agency]).like(search_term))
            if f_name in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_name]).like(search_term))
            clauses.append(or_(*search_clauses))

        if clauses:
            stmt = stmt.where(and_(*clauses))

        result = self.db.execute(stmt).fetchall()
        rows = []
        for r in result:
            rd = dict(r._mapping)
            rd["faculty_email"] = str(rd.get("f_email") or rd.get("pr_faculty_email") or "").lower().strip()
            rd["amount"] = float(rd.get("amount") or 0.0)
            rd["score"] = float(rd.get("score") or 0.0)
            rows.append(rd)
        return rows

    def _get_all_projects(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        int_table, ext_table, _, _ = self._get_tables()
        internal_rows = self._get_filtered_projects(int_table, False, filters)
        external_rows = self._get_filtered_projects(ext_table, True, filters)
        return internal_rows + external_rows

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 1: GET /overview"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        total_active_faculty = len({p["email"] for p in active_faculty_profiles if p["email"]})

        all_projects = self._get_all_projects(filters)
        proposals = self._get_filtered_proposals(filters)

        funded_project_count = len(all_projects)
        proposal_count = len(proposals)

        total_sanctioned_funding = round(sum(r["amount"] for r in all_projects), 2)
        total_proposed_funding = round(sum(r["amount"] for r in proposals), 2)

        external_funding = round(sum(r["amount"] for r in all_projects if r.get("is_external")), 2)

        avg_project_amount = round(total_sanctioned_funding / funded_project_count, 2) if funded_project_count > 0 else 0.0
        avg_proposal_amount = round(total_proposed_funding / proposal_count, 2) if proposal_count > 0 else 0.0

        ext_funding_pct = round((external_funding / total_sanctioned_funding * 100.0), 2) if total_sanctioned_funding > 0 else 0.0

        funding_per_active = round(total_sanctioned_funding / total_active_faculty, 2) if total_active_faculty > 0 else 0.0

        funded_emails = {r["faculty_email"] for r in all_projects if r.get("faculty_email")}
        faculty_receiving_funding = len(funded_emails)

        funding_per_funded = round(total_sanctioned_funding / faculty_receiving_funding, 2) if faculty_receiving_funding > 0 else 0.0

        pi_emails = {r["faculty_email"] for r in all_projects if r.get("normalized_role") == "Principal Investigator" and r.get("faculty_email")}
        principal_investigator_count = len(pi_emails)

        ongoing_projects = sum(1 for r in all_projects if r.get("normalized_status") in ("Ongoing", "Sanctioned"))
        completed_projects = sum(1 for r in all_projects if r.get("normalized_status") == "Completed")

        prop_to_proj_indicator = round((funded_project_count / proposal_count * 100.0), 2) if proposal_count > 0 else 0.0

        return {
            "total_sanctioned_funding": total_sanctioned_funding,
            "total_proposed_funding": total_proposed_funding,
            "funded_project_count": funded_project_count,
            "proposal_count": proposal_count,
            "average_project_amount": avg_project_amount,
            "average_proposal_amount": avg_proposal_amount,
            "external_funding_percentage": ext_funding_pct,
            "funding_per_active_faculty": funding_per_active,
            "funding_per_funded_faculty": funding_per_funded,
            "faculty_receiving_project_funding": faculty_receiving_funding,
            "principal_investigator_count": principal_investigator_count,
            "ongoing_projects": ongoing_projects,
            "completed_projects": completed_projects,
            "proposal_to_project_indicator": prop_to_proj_indicator,
            "proposal_to_project_indicator_note": "Approximate indicator because proposals and projects do not share a proposal identifier.",
        }

    def projects(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 2: GET /projects (Internal)"""
        int_table, _, _, _ = self._get_tables()
        rows = self._get_filtered_projects(int_table, False, filters)

        sort_by = filters.get("sort_by") or "title"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        numeric_fields = ["id", "amount", "score", "hod_score", "director_score", "dean_score", "vc_score", "final_validated_score"]
        if sort_by in numeric_fields:
            rows.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            rows.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_recs = len(rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return {
            "total": total_recs,
            "page": page,
            "page_size": page_size,
            "items": rows[start_idx:end_idx],
        }

    def external_projects(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 3: GET /external-projects"""
        _, ext_table, _, _ = self._get_tables()
        rows = self._get_filtered_projects(ext_table, True, filters)

        sort_by = filters.get("sort_by") or "title"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        numeric_fields = ["id", "amount", "score", "hod_score", "director_score", "dean_score", "vc_score", "final_validated_score"]
        if sort_by in numeric_fields:
            rows.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            rows.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_recs = len(rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return {
            "total": total_recs,
            "page": page,
            "page_size": page_size,
            "items": rows[start_idx:end_idx],
        }

    def proposals(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 4: GET /proposals"""
        rows = self._get_filtered_proposals(filters)

        sort_by = filters.get("sort_by") or "title"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        if sort_by in ["id", "amount", "score"]:
            rows.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            rows.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_recs = len(rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return {
            "total": total_recs,
            "page": page,
            "page_size": page_size,
            "items": rows[start_idx:end_idx],
        }

    def funding_agencies(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Endpoint 5: GET /funding-agencies"""
        all_projects = self._get_all_projects(filters)
        proposals = self._get_filtered_proposals(filters)

        agency_stats: Dict[str, Dict[str, Any]] = {}

        for r in all_projects:
            ag = str(r.get("agency") or "Unspecified").strip()
            agency_stats.setdefault(ag, {
                "agency": ag,
                "funded_project_count": 0,
                "proposal_count": 0,
                "total_sanctioned_amount": 0.0,
                "total_proposed_amount": 0.0,
                "faculty_set": set(),
            })
            agency_stats[ag]["funded_project_count"] += 1
            agency_stats[ag]["total_sanctioned_amount"] += r["amount"]
            if r.get("faculty_email"):
                agency_stats[ag]["faculty_set"].add(r["faculty_email"])

        for r in proposals:
            ag = str(r.get("agency") or "Unspecified").strip()
            agency_stats.setdefault(ag, {
                "agency": ag,
                "funded_project_count": 0,
                "proposal_count": 0,
                "total_sanctioned_amount": 0.0,
                "total_proposed_amount": 0.0,
                "faculty_set": set(),
            })
            agency_stats[ag]["proposal_count"] += 1
            agency_stats[ag]["total_proposed_amount"] += r["amount"]
            if r.get("faculty_email"):
                agency_stats[ag]["faculty_set"].add(r["faculty_email"])

        result = []
        for ag, data in sorted(agency_stats.items(), key=lambda x: x[1]["total_sanctioned_amount"], reverse=True):
            p_cnt = data["funded_project_count"]
            s_amt = round(data["total_sanctioned_amount"], 2)
            avg_amt = round(s_amt / p_cnt, 2) if p_cnt > 0 else 0.0
            result.append({
                "agency": ag,
                "funded_project_count": p_cnt,
                "proposal_count": data["proposal_count"],
                "total_sanctioned_amount": s_amt,
                "total_proposed_amount": round(data["total_proposed_amount"], 2),
                "average_project_amount": avg_amt,
                "faculty_count": len(data["faculty_set"]),
            })
        return result

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 6: GET /departments"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        dept_active_fac: Dict[Tuple[str, str], Set[str]] = {}
        for p in active_faculty_profiles:
            s = p.get("school") or "Unassigned"
            d = p.get("department") or "Unassigned"
            dept_active_fac.setdefault((s, d), set()).add(p["email"])

        all_projects = self._get_all_projects(filters)
        proposals = self._get_filtered_proposals(filters)

        dept_projects: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for r in all_projects:
            s = r.get("school") or "Unassigned"
            d = r.get("department") or "Unassigned"
            dept_projects.setdefault((s, d), []).append(r)

        dept_proposals: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for r in proposals:
            s = r.get("school") or "Unassigned"
            d = r.get("department") or "Unassigned"
            dept_proposals.setdefault((s, d), []).append(r)

        all_keys = set(dept_active_fac.keys()).union(dept_projects.keys()).union(dept_proposals.keys())

        dept_items = []
        for key in sorted(all_keys):
            school, department = key
            active_fac_count = len(dept_active_fac.get(key, set()))
            p_rows = dept_projects.get(key, [])
            pr_rows = dept_proposals.get(key, [])

            funded_project_count = len(p_rows)
            proposal_count = len(pr_rows)

            total_sanctioned_funding = round(sum(r["amount"] for r in p_rows), 2)
            total_proposed_funding = round(sum(r["amount"] for r in pr_rows), 2)
            external_funding = round(sum(r["amount"] for r in p_rows if r.get("is_external")), 2)

            avg_project_amount = round(total_sanctioned_funding / funded_project_count, 2) if funded_project_count > 0 else 0.0

            funded_emails = {r["faculty_email"] for r in p_rows if r.get("faculty_email")}
            faculty_receiving_funding = len(funded_emails)

            pi_emails = {r["faculty_email"] for r in p_rows if r.get("normalized_role") == "Principal Investigator" and r.get("faculty_email")}
            principal_investigator_count = len(pi_emails)

            ongoing_projects = sum(1 for r in p_rows if r.get("normalized_status") in ("Ongoing", "Sanctioned"))
            completed_projects = sum(1 for r in p_rows if r.get("normalized_status") == "Completed")

            dept_items.append({
                "school": school,
                "department": department,
                "active_faculty": active_fac_count,
                "funded_project_count": funded_project_count,
                "proposal_count": proposal_count,
                "total_sanctioned_funding": total_sanctioned_funding,
                "total_proposed_funding": total_proposed_funding,
                "external_funding": external_funding,
                "average_project_amount": avg_project_amount,
                "faculty_receiving_funding": faculty_receiving_funding,
                "principal_investigator_count": principal_investigator_count,
                "ongoing_projects": ongoing_projects,
                "completed_projects": completed_projects,
            })

        # Sorting
        sort_by = filters.get("sort_by") or "total_sanctioned_funding"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        if sort_by in ["active_faculty", "funded_project_count", "proposal_count", "total_sanctioned_funding", "total_proposed_funding", "external_funding", "average_project_amount", "faculty_receiving_funding", "principal_investigator_count", "ongoing_projects", "completed_projects"]:
            dept_items.sort(key=lambda x: x.get(sort_by) or 0, reverse=reverse)
        else:
            dept_items.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_depts = len(dept_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return {
            "total": total_depts,
            "page": page,
            "page_size": page_size,
            "items": dept_items[start_idx:end_idx],
        }

    def faculty(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 7: GET /faculty"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        active_email_map = {p["email"]: p for p in active_faculty_profiles if p["email"]}

        all_projects = self._get_all_projects(filters)
        proposals = self._get_filtered_proposals(filters)

        fac_projects: Dict[str, List[Dict[str, Any]]] = {}
        for r in all_projects:
            fe = r.get("faculty_email")
            if fe:
                fac_projects.setdefault(fe, []).append(r)

        fac_proposals: Dict[str, List[Dict[str, Any]]] = {}
        for r in proposals:
            fe = r.get("faculty_email")
            if fe:
                fac_proposals.setdefault(fe, []).append(r)

        all_emails = set(active_email_map.keys()).union(fac_projects.keys()).union(fac_proposals.keys())

        faculty_items = []
        for email in sorted(all_emails):
            prof = active_email_map.get(email, {})
            p_rows = fac_projects.get(email, [])
            pr_rows = fac_proposals.get(email, [])

            name = prof.get("faculty_name") or (p_rows[0].get("faculty_name") if p_rows else (pr_rows[0].get("faculty_name") if pr_rows else "Unknown"))
            emp_id = prof.get("employee_id") or (p_rows[0].get("employee_id") if p_rows else (pr_rows[0].get("employee_id") if pr_rows else "N/A"))
            sch = prof.get("school") or (p_rows[0].get("school") if p_rows else (pr_rows[0].get("school") if pr_rows else "N/A"))
            dept = prof.get("department") or (p_rows[0].get("department") if p_rows else (pr_rows[0].get("department") if pr_rows else "N/A"))
            desig = prof.get("designation") or (p_rows[0].get("designation") if p_rows else (pr_rows[0].get("designation") if pr_rows else "N/A"))

            funded_project_count = len(p_rows)
            proposal_count = len(pr_rows)

            total_sanctioned_funding = round(sum(r["amount"] for r in p_rows), 2)
            total_proposed_funding = round(sum(r["amount"] for r in pr_rows), 2)

            pi_projects = sum(1 for r in p_rows if r.get("normalized_role") == "Principal Investigator")
            co_i_projects = sum(1 for r in p_rows if r.get("normalized_role") in ("Co-Principal Investigator", "Co-Investigator"))

            ongoing_projects = sum(1 for r in p_rows if r.get("normalized_status") in ("Ongoing", "Sanctioned"))
            completed_projects = sum(1 for r in p_rows if r.get("normalized_status") == "Completed")

            val_scores = [float(r.get("final_validated_score") or 0.0) for r in p_rows]
            latest_val_score = round(val_scores[-1], 2) if val_scores else 0.0

            faculty_items.append({
                "faculty_email": email,
                "faculty_name": name,
                "employee_id": emp_id,
                "department": dept,
                "school": sch,
                "designation": desig,
                "funded_project_count": funded_project_count,
                "proposal_count": proposal_count,
                "total_sanctioned_funding": total_sanctioned_funding,
                "total_proposed_funding": total_proposed_funding,
                "principal_investigator_projects": pi_projects,
                "co_investigator_projects": co_i_projects,
                "ongoing_projects": ongoing_projects,
                "completed_projects": completed_projects,
                "latest_validated_score": latest_val_score,
            })

        # Sorting
        sort_by = filters.get("sort_by") or "total_sanctioned_funding"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        if sort_by in ["funded_project_count", "proposal_count", "total_sanctioned_funding", "total_proposed_funding", "principal_investigator_projects", "co_investigator_projects", "ongoing_projects", "completed_projects", "latest_validated_score"]:
            faculty_items.sort(key=lambda x: x.get(sort_by) or 0, reverse=reverse)
        else:
            faculty_items.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_fac = len(faculty_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return {
            "total": total_fac,
            "page": page,
            "page_size": page_size,
            "items": faculty_items[start_idx:end_idx],
        }

    def trends(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 8: GET /trends"""
        all_projects = self._get_all_projects(filters)
        proposals = self._get_filtered_proposals(filters)

        proj_by_year: Dict[str, Dict[str, Any]] = {}
        for r in all_projects:
            yr_num = parse_numeric_year(r.get("sanction_date") or r.get("academic_year"))
            yr_str = str(yr_num) if yr_num else "Unspecified"
            proj_by_year.setdefault(yr_str, {"sanctioned_amount": 0.0, "project_count": 0})
            proj_by_year[yr_str]["sanctioned_amount"] += r["amount"]
            proj_by_year[yr_str]["project_count"] += 1

        prop_by_year: Dict[str, Dict[str, Any]] = {}
        for r in proposals:
            yr_num = parse_numeric_year(r.get("academic_year"))
            yr_str = str(yr_num) if yr_num else "Unspecified"
            prop_by_year.setdefault(yr_str, {"proposed_amount": 0.0, "proposal_count": 0})
            prop_by_year[yr_str]["proposed_amount"] += r["amount"]
            prop_by_year[yr_str]["proposal_count"] += 1

        all_years = sorted(
            list(set(proj_by_year.keys()).union(prop_by_year.keys())),
            key=lambda y: int(y) if y.isdigit() else 0
        )

        funding_trend_by_sanction_date = [
            {
                "year": yr,
                "sanctioned_amount": round(proj_by_year.get(yr, {}).get("sanctioned_amount", 0.0), 2),
                "project_count": proj_by_year.get(yr, {}).get("project_count", 0),
            }
            for yr in all_years if yr != "Unspecified"
        ]

        proposal_trend_by_academic_year = [
            {
                "year": yr,
                "proposed_amount": round(prop_by_year.get(yr, {}).get("proposed_amount", 0.0), 2),
                "proposal_count": prop_by_year.get(yr, {}).get("proposal_count", 0),
            }
            for yr in all_years if yr != "Unspecified"
        ]

        yoy_growth = []
        for i, yr in enumerate(all_years):
            if not yr.isdigit():
                continue
            if i > 0 and all_years[i - 1].isdigit():
                prev_yr = all_years[i - 1]
                c_amt = proj_by_year.get(yr, {}).get("sanctioned_amount", 0.0)
                p_amt = proj_by_year.get(prev_yr, {}).get("sanctioned_amount", 0.0)
                gr = round(((c_amt - p_amt) / p_amt * 100.0), 2) if p_amt > 0 else (100.0 if c_amt > 0 else 0.0)
                yoy_growth.append({"year": yr, "growth_rate": gr})
            else:
                yoy_growth.append({"year": yr, "growth_rate": 0.0})

        return {
            "funding_trend_by_sanction_date": funding_trend_by_sanction_date,
            "proposal_trend_by_academic_year": proposal_trend_by_academic_year,
            "year_over_year_funding_growth": yoy_growth,
        }

    def concentration(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 9: GET /concentration"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        active_emails = {p["email"] for p in active_faculty_profiles if p["email"]}

        all_projects = self._get_all_projects(filters)
        proposals = self._get_filtered_proposals(filters)

        total_sanctioned = sum(r["amount"] for r in all_projects)

        fac_funding: Dict[str, float] = {}
        fac_names: Dict[str, Tuple[str, str]] = {}
        dept_funding: Dict[str, float] = {}

        role_counts = {"pi_count": 0, "co_pi_count": 0, "co_i_count": 0, "other_count": 0}
        ongoing_cnt = 0
        completed_cnt = 0

        funded_depts = set()
        funded_fac_emails = set()

        for r in all_projects:
            fe = r.get("faculty_email")
            if fe:
                fac_funding[fe] = fac_funding.get(fe, 0.0) + r["amount"]
                fac_names[fe] = (r.get("faculty_name") or "Unknown", r.get("department") or "Unassigned")
                funded_fac_emails.add(fe)

            d = r.get("department")
            if d:
                dept_funding[d] = dept_funding.get(d, 0.0) + r["amount"]
                funded_depts.add(d)

            nr = r.get("normalized_role")
            if nr == "Principal Investigator":
                role_counts["pi_count"] += 1
            elif nr == "Co-Principal Investigator":
                role_counts["co_pi_count"] += 1
            elif nr == "Co-Investigator":
                role_counts["co_i_count"] += 1
            else:
                role_counts["other_count"] += 1

            ns = r.get("normalized_status")
            if ns in ("Ongoing", "Sanctioned"):
                ongoing_cnt += 1
            elif ns == "Completed":
                completed_cnt += 1

        top_5_fac_amt = sum(sorted(fac_funding.values(), reverse=True)[:5])
        top_5_dept_amt = sum(sorted(dept_funding.values(), reverse=True)[:5])

        top_5_fac_share = round((top_5_fac_amt / total_sanctioned * 100.0), 2) if total_sanctioned > 0 else 0.0
        top_5_dept_share = round((top_5_dept_amt / total_sanctioned * 100.0), 2) if total_sanctioned > 0 else 0.0

        highest_funded_fac = []
        for fe, amt in sorted(fac_funding.items(), key=lambda x: x[1], reverse=True)[:5]:
            fname, dname = fac_names.get(fe, ("Unknown", "Unassigned"))
            highest_funded_fac.append({
                "faculty_name": fname,
                "department": dname,
                "total_funding": round(amt, 2),
            })

        proposal_depts = {r.get("department") for r in proposals if r.get("department")}
        proposal_fac_emails = {r.get("faculty_email") for r in proposals if r.get("faculty_email")}

        depts_with_prop_no_fund = sorted(list(proposal_depts - funded_depts))
        fac_with_prop_no_fund = sorted(list(proposal_fac_emails - funded_fac_emails))

        # Schools with no external projects
        all_schools = {p.get("school") for p in active_faculty_profiles if p.get("school")}
        ext_schools = {r.get("school") for r in all_projects if r.get("is_external") and r.get("school")}
        schools_with_no_ext = sorted(list(all_schools - ext_schools))

        ratio = round((ongoing_cnt / completed_cnt), 2) if completed_cnt > 0 else 0.0

        return {
            "top_five_faculty_funding_share": top_5_fac_share,
            "top_five_department_funding_share": top_5_dept_share,
            "faculty_with_highest_funding": highest_funded_fac,
            "departments_with_proposals_but_no_funded_projects": depts_with_prop_no_fund,
            "faculty_with_proposals_but_no_funded_projects": fac_with_prop_no_fund,
            "schools_with_no_external_projects": schools_with_no_ext,
            "pi_versus_coinvestigator_participation": role_counts,
            "ongoing_versus_completed_project_ratio": ratio,
        }

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Endpoint 10: GET /export"""
        int_table, ext_table, _, _ = self._get_tables()
        internal_rows = self._get_filtered_projects(int_table, False, filters)
        external_rows = self._get_filtered_projects(ext_table, True, filters)
        proposal_rows = self._get_filtered_proposals(filters)

        export_rows = []
        for r in internal_rows:
            export_rows.append({
                "Record Type": "Internal Project",
                "ID": r.get("id"),
                "Faculty Email": r.get("faculty_email"),
                "Faculty Name": r.get("faculty_name"),
                "Employee ID": r.get("employee_id"),
                "Department": r.get("department"),
                "School": r.get("school"),
                "Title": r.get("title"),
                "Agency": r.get("agency"),
                "Sanction Date": r.get("sanction_date"),
                "Amount": r.get("amount"),
                "Role": r.get("role"),
                "Normalized Role": r.get("normalized_role"),
                "Project Status": r.get("project_status"),
                "Normalized Status": r.get("normalized_status"),
                "Academic Year": r.get("academic_year"),
                "Self Score": r.get("score"),
                "HOD Score": r.get("hod_score"),
                "Director Score": r.get("director_score"),
                "Dean Score": r.get("dean_score"),
                "VC Score": r.get("vc_score"),
                "Final Validated Score": r.get("final_validated_score"),
            })

        for r in external_rows:
            export_rows.append({
                "Record Type": "External Project",
                "ID": r.get("id"),
                "Faculty Email": r.get("faculty_email"),
                "Faculty Name": r.get("faculty_name"),
                "Employee ID": r.get("employee_id"),
                "Department": r.get("department"),
                "School": r.get("school"),
                "Title": r.get("title"),
                "Agency": r.get("agency"),
                "Sanction Date": r.get("sanction_date"),
                "Amount": r.get("amount"),
                "Role": r.get("role"),
                "Normalized Role": r.get("normalized_role"),
                "Project Status": r.get("project_status"),
                "Normalized Status": r.get("normalized_status"),
                "Academic Year": r.get("academic_year"),
                "Self Score": r.get("score"),
                "HOD Score": r.get("hod_score"),
                "Director Score": r.get("director_score"),
                "Dean Score": r.get("dean_score"),
                "VC Score": r.get("vc_score"),
                "Final Validated Score": r.get("final_validated_score"),
            })

        for r in proposal_rows:
            export_rows.append({
                "Record Type": "Proposal",
                "ID": r.get("id"),
                "Faculty Email": r.get("faculty_email"),
                "Faculty Name": r.get("faculty_name"),
                "Employee ID": r.get("employee_id"),
                "Department": r.get("department"),
                "School": r.get("school"),
                "Title": r.get("title"),
                "Agency": r.get("agency"),
                "Sanction Date": "N/A",
                "Amount": r.get("amount"),
                "Role": "N/A",
                "Normalized Role": "N/A",
                "Project Status": "Proposed",
                "Normalized Status": "Proposed",
                "Academic Year": r.get("academic_year"),
                "Self Score": r.get("score"),
                "HOD Score": 0.0,
                "Director Score": 0.0,
                "Dean Score": 0.0,
                "VC Score": 0.0,
                "Final Validated Score": r.get("score"),
            })

        return export_rows
