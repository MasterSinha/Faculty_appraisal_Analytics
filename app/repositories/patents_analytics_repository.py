import datetime
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import Table, and_, case, distinct, func, or_, select, text
from sqlalchemy.orm import Session

from app.core.constants import (
    DEPARTMENT_COLUMNS,
    EMAIL_COLUMNS,
    EMPLOYEE_COLUMNS,
    NAME_COLUMNS,
    SCHOOL_COLUMNS,
    TITLE_COLUMNS,
    YEAR_COLUMNS,
)
from app.models.schema_reflector import SchemaReflector


def normalize_status(raw_status: Optional[str]) -> str:
    if not raw_status or not str(raw_status).strip():
        return "Unknown"
    s = str(raw_status).strip().lower()
    if "grant" in s:
        return "Granted"
    if "fil" in s or "submit" in s or "appli" in s or "appl" in s:
        return "Filed"
    if "pub" in s:
        return "Published"
    if "pend" in s or "wait" in s or "process" in s or "review" in s or "under" in s:
        return "Pending"
    if "reject" in s or "refus" in s or "abandon" in s:
        return "Rejected"
    if "expir" in s or "laps" in s:
        return "Expired"
    return "Unknown"



def normalize_scope(raw_scope: Optional[str]) -> str:
    if not raw_scope or not str(raw_scope).strip():
        return "Unknown"
    sc = str(raw_scope).strip().lower()
    if any(term in sc for term in ["domestic", "national", "india", "indian"]):
        return "Domestic"
    if any(term in sc for term in ["international", "foreign", "global", "pct", "us", "usa", "ep", "wipo", "eu"]):
        return "International"
    return "Unknown"


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


class PatentsAnalyticsRepository:
    """Repository for Patents and IPR Analytics using SQLAlchemy Core."""

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
        patent_table = self._logical_table(["patents"])
        ipr_table = self._logical_table(["ipr_records"])
        faculty_table = self._logical_table(["faculty_profiles", "faculty", "users"])
        journal_table = self._logical_table(["journal_publications", "journals"])
        return patent_table, ipr_table, faculty_table, journal_table

    def _get_active_faculty_profiles(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        _, _, faculty_table, _ = self._get_tables()
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

        if filters.get("school") and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])
        if filters.get("department") and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])
        if filters.get("designation") and f_desig in faculty_table.c:
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

    def _get_filtered_patents(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        patent_table, _, faculty_table, _ = self._get_tables()
        if patent_table is None or faculty_table is None:
            return []

        p_cols = SchemaReflector.column_names(patent_table)
        f_cols = SchemaReflector.column_names(faculty_table)

        p_id = SchemaReflector.first_existing(p_cols, ["id", "patent_id"]) or "id"
        p_email = SchemaReflector.first_existing(p_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        p_title = SchemaReflector.first_existing(p_cols, TITLE_COLUMNS) or "title"
        p_type = SchemaReflector.first_existing(p_cols, ["type", "patent_type"]) or "type"
        p_scope = SchemaReflector.first_existing(p_cols, ["scope", "patent_scope"]) or "scope"
        p_date = SchemaReflector.first_existing(p_cols, ["patent_date", "date", "filing_date", "publication_date"]) or "patent_date"
        p_status = SchemaReflector.first_existing(p_cols, ["patent_status", "status"]) or "patent_status"
        p_file_no = SchemaReflector.first_existing(p_cols, ["file_no", "application_no", "patent_no", "file_number"]) or "file_no"
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
            patent_table.c[p_id].label("id") if p_id in patent_table.c else patent_table.c[p_cols[0]].label("id"),
            patent_table.c[p_email].label("p_faculty_email") if p_email in patent_table.c else text("''").label("p_faculty_email"),
            patent_table.c[p_title].label("title") if p_title in patent_table.c else text("''").label("title"),
            patent_table.c[p_type].label("type") if p_type in patent_table.c else text("''").label("type"),
            patent_table.c[p_scope].label("scope") if p_scope in patent_table.c else text("''").label("scope"),
            patent_table.c[p_date].label("patent_date") if p_date in patent_table.c else text("NULL").label("patent_date"),
            patent_table.c[p_status].label("patent_status") if p_status in patent_table.c else text("''").label("patent_status"),
            patent_table.c[p_file_no].label("file_no") if p_file_no in patent_table.c else text("''").label("file_no"),
            patent_table.c[p_year].label("academic_year") if p_year in patent_table.c else text("''").label("academic_year"),
            patent_table.c[p_score].label("score") if p_score in patent_table.c else text("0.0").label("score"),
            patent_table.c[p_hod].label("hod_score") if p_hod in patent_table.c else text("0.0").label("hod_score"),
            patent_table.c[p_dir].label("director_score") if p_dir in patent_table.c else text("0.0").label("director_score"),
            patent_table.c[p_dean].label("dean_score") if p_dean in patent_table.c else text("0.0").label("dean_score"),
            patent_table.c[p_vc].label("vc_score") if p_vc in patent_table.c else text("0.0").label("vc_score"),
            faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else text("''").label("f_email"),
            faculty_table.c[f_name].label("faculty_name") if f_name in faculty_table.c else text("''").label("faculty_name"),
            faculty_table.c[f_emp].label("employee_id") if f_emp in faculty_table.c else text("''").label("employee_id"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else text("''").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else text("''").label("school"),
            faculty_table.c[f_desig].label("designation") if f_desig in faculty_table.c else text("''").label("designation"),
        ]

        stmt = select(*select_fields)
        p_email_col = patent_table.c[p_email] if p_email in patent_table.c else patent_table.c[p_cols[0]]
        f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]

        join_clause = func.lower(func.trim(p_email_col)) == func.lower(func.trim(f_email_col))
        stmt = stmt.select_from(patent_table.join(faculty_table, join_clause))

        clauses = []
        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        # VALID PATENT CONDITION: title IS NOT NULL AND TRIM(title) <> ''
        p_title_col = patent_table.c[p_title] if p_title in patent_table.c else patent_table.c[p_cols[0]]
        clauses.append(p_title_col.isnot(None))
        clauses.append(func.trim(p_title_col) != "")

        if filters.get("academic_year") and p_year in patent_table.c:
            clauses.append(func.cast(patent_table.c[p_year], text("VARCHAR")) == str(filters["academic_year"]))

        if filters.get("school") and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])

        if filters.get("department") and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])

        if filters.get("designation") and f_desig in faculty_table.c:
            clauses.append(faculty_table.c[f_desig] == filters["designation"])

        if filters.get("faculty_email"):
            target_email = str(filters["faculty_email"]).lower().strip()
            clauses.append(func.lower(func.trim(f_email_col)) == target_email)

        if filters.get("search"):
            search_term = f"%{str(filters['search']).lower().strip()}%"
            search_clauses = [
                func.lower(p_title_col).like(search_term),
                func.lower(f_email_col).like(search_term),
            ]
            if p_file_no in patent_table.c:
                search_clauses.append(func.lower(patent_table.c[p_file_no]).like(search_term))
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
            rd["normalized_status"] = normalize_status(rd.get("patent_status"))
            rd["normalized_scope"] = normalize_scope(rd.get("scope"))

            # Filter by status / scope if provided
            if filters.get("status") and rd["normalized_status"].lower() != str(filters["status"]).lower().strip():
                continue
            if filters.get("scope") and rd["normalized_scope"].lower() != str(filters["scope"]).lower().strip():
                continue

            vc = float(rd.get("vc_score") or 0.0)
            dn = float(rd.get("dean_score") or 0.0)
            dr = float(rd.get("director_score") or 0.0)
            hd = float(rd.get("hod_score") or 0.0)
            sc = float(rd.get("score") or 0.0)
            final_score = vc if vc > 0 else (dn if dn > 0 else (dr if dr > 0 else (hd if hd > 0 else sc)))
            rd["final_validated_score"] = float(final_score)
            rd["score"] = float(sc)
            rd["hod_score"] = float(hd)
            rd["director_score"] = float(dr)
            rd["dean_score"] = float(dn)
            rd["vc_score"] = float(vc)

            # Quality flags
            flags = []
            if not rd.get("patent_status") or rd["normalized_status"] == "Unknown":
                flags.append("missing_status")
            if not rd.get("file_no") or str(rd.get("file_no")).strip() == "":
                flags.append("missing_file_no")
            p_date_val = rd.get("patent_date")
            if p_date_val:
                try:
                    p_date_obj = p_date_val if isinstance(p_date_val, (datetime.date, datetime.datetime)) else datetime.date.fromisoformat(str(p_date_val)[:10])
                    if p_date_obj > datetime.date.today():
                        flags.append("future_date")
                except Exception:
                    pass
            rd["flags"] = flags

            rows.append(rd)
        return rows

    def _get_filtered_ipr(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        _, ipr_table, faculty_table, _ = self._get_tables()
        if ipr_table is None or faculty_table is None:
            return []

        i_cols = SchemaReflector.column_names(ipr_table)
        f_cols = SchemaReflector.column_names(faculty_table)

        i_id = SchemaReflector.first_existing(i_cols, ["id", "ipr_id"]) or "id"
        i_email = SchemaReflector.first_existing(i_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        i_title = SchemaReflector.first_existing(i_cols, TITLE_COLUMNS) or "title"
        i_scope = SchemaReflector.first_existing(i_cols, ["scope", "ipr_scope"]) or "scope"
        i_date = SchemaReflector.first_existing(i_cols, ["ipr_date", "date", "registration_date"]) or "ipr_date"
        i_status = SchemaReflector.first_existing(i_cols, ["ipr_status", "status"]) or "ipr_status"
        i_file_no = SchemaReflector.first_existing(i_cols, ["file_no", "application_no", "ipr_no", "registration_no"]) or "file_no"
        i_score = SchemaReflector.first_existing(i_cols, ["score", "self_score"]) or "score"

        f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
        f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
        f_emp = SchemaReflector.first_existing(f_cols, EMPLOYEE_COLUMNS) or "employee_id"
        f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
        f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"
        f_desig = SchemaReflector.first_existing(f_cols, ["designation", "role"]) or "designation"

        select_fields = [
            ipr_table.c[i_id].label("id") if i_id in ipr_table.c else ipr_table.c[i_cols[0]].label("id"),
            ipr_table.c[i_email].label("i_faculty_email") if i_email in ipr_table.c else text("''").label("i_faculty_email"),
            ipr_table.c[i_title].label("title") if i_title in ipr_table.c else text("''").label("title"),
            ipr_table.c[i_scope].label("scope") if i_scope in ipr_table.c else text("''").label("scope"),
            ipr_table.c[i_date].label("ipr_date") if i_date in ipr_table.c else text("NULL").label("ipr_date"),
            ipr_table.c[i_status].label("ipr_status") if i_status in ipr_table.c else text("''").label("ipr_status"),
            ipr_table.c[i_file_no].label("file_no") if i_file_no in ipr_table.c else text("''").label("file_no"),
            ipr_table.c[i_score].label("score") if i_score in ipr_table.c else text("0.0").label("score"),
            faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else text("''").label("f_email"),
            faculty_table.c[f_name].label("faculty_name") if f_name in faculty_table.c else text("''").label("faculty_name"),
            faculty_table.c[f_emp].label("employee_id") if f_emp in faculty_table.c else text("''").label("employee_id"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else text("''").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else text("''").label("school"),
            faculty_table.c[f_desig].label("designation") if f_desig in faculty_table.c else text("''").label("designation"),
        ]

        stmt = select(*select_fields)
        i_email_col = ipr_table.c[i_email] if i_email in ipr_table.c else ipr_table.c[i_cols[0]]
        f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]

        join_clause = func.lower(func.trim(i_email_col)) == func.lower(func.trim(f_email_col))
        stmt = stmt.select_from(ipr_table.join(faculty_table, join_clause))

        clauses = []
        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        # VALID IPR CONDITION: title IS NOT NULL AND TRIM(title) <> ''
        i_title_col = ipr_table.c[i_title] if i_title in ipr_table.c else ipr_table.c[i_cols[0]]
        clauses.append(i_title_col.isnot(None))
        clauses.append(func.trim(i_title_col) != "")

        if filters.get("school") and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])

        if filters.get("department") and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])

        if filters.get("designation") and f_desig in faculty_table.c:
            clauses.append(faculty_table.c[f_desig] == filters["designation"])

        if filters.get("faculty_email"):
            target_email = str(filters["faculty_email"]).lower().strip()
            clauses.append(func.lower(func.trim(f_email_col)) == target_email)

        if filters.get("search"):
            search_term = f"%{str(filters['search']).lower().strip()}%"
            search_clauses = [
                func.lower(i_title_col).like(search_term),
                func.lower(f_email_col).like(search_term),
            ]
            if i_file_no in ipr_table.c:
                search_clauses.append(func.lower(ipr_table.c[i_file_no]).like(search_term))
            if f_name in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_name]).like(search_term))
            clauses.append(or_(*search_clauses))

        if clauses:
            stmt = stmt.where(and_(*clauses))

        result = self.db.execute(stmt).fetchall()
        rows = []
        for r in result:
            rd = dict(r._mapping)
            rd["faculty_email"] = str(rd.get("f_email") or rd.get("i_faculty_email") or "").lower().strip()
            rd["normalized_status"] = normalize_status(rd.get("ipr_status"))
            rd["normalized_scope"] = normalize_scope(rd.get("scope"))

            if filters.get("status") and rd["normalized_status"].lower() != str(filters["status"]).lower().strip():
                continue
            if filters.get("scope") and rd["normalized_scope"].lower() != str(filters["scope"]).lower().strip():
                continue

            rd["score"] = float(rd.get("score") or 0.0)

            flags = []
            if not rd.get("ipr_status") or rd["normalized_status"] == "Unknown":
                flags.append("missing_status")
            if not rd.get("file_no") or str(rd.get("file_no")).strip() == "":
                flags.append("missing_file_no")
            rd["flags"] = flags

            rows.append(rd)
        return rows

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 1: GET /overview"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        total_active_faculty = len({p["email"] for p in active_faculty_profiles if p["email"]})

        patent_rows = self._get_filtered_patents(filters)
        ipr_rows = self._get_filtered_ipr(filters)

        total_valid_patents = len(patent_rows)
        total_ipr_records = len(ipr_rows)

        patent_filing_emails = {r["faculty_email"] for r in patent_rows if r.get("faculty_email")}
        patent_filing_faculty = len(patent_filing_emails)

        patents_granted = sum(1 for r in patent_rows if r.get("normalized_status") == "Granted")
        patents_pending = sum(1 for r in patent_rows if r.get("normalized_status") in ("Pending", "Filed"))

        patent_grant_rate = round((patents_granted / total_valid_patents * 100.0), 2) if total_valid_patents > 0 else 0.0
        patents_per_active = round((total_valid_patents / total_active_faculty), 2) if total_active_faculty > 0 else 0.0
        patent_participation_rate = round((patent_filing_faculty / total_active_faculty * 100.0), 2) if total_active_faculty > 0 else 0.0

        patent_scores = [float(r.get("score") or 0.0) for r in patent_rows]
        val_patent_scores = [float(r.get("final_validated_score") or 0.0) for r in patent_rows]

        average_patent_score = round(sum(patent_scores) / len(patent_scores), 2) if patent_scores else 0.0
        average_validated_patent_score = round(sum(val_patent_scores) / len(val_patent_scores), 2) if val_patent_scores else 0.0

        # Faculty with multiple patents (>= 2)
        fac_patent_counts: Dict[str, int] = {}
        for r in patent_rows:
            fe = r.get("faculty_email")
            if fe:
                fac_patent_counts[fe] = fac_patent_counts.get(fe, 0) + 1
        faculty_with_multiple_patents = sum(1 for cnt in fac_patent_counts.values() if cnt >= 2)

        # Faculty with journal papers but no patents
        _, _, _, journal_table = self._get_tables()
        faculty_with_journal_papers_but_no_patents = 0
        if journal_table is not None:
            j_cols = SchemaReflector.column_names(journal_table)
            j_email = SchemaReflector.first_existing(j_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
            j_title = SchemaReflector.first_existing(j_cols, TITLE_COLUMNS) or "title"

            j_stmt = select(distinct(func.lower(func.trim(journal_table.c[j_email]))))
            j_stmt = j_stmt.where(and_(journal_table.c[j_title].isnot(None), func.trim(journal_table.c[j_title]) != ""))
            journal_fac_emails = {str(r[0]).lower().strip() for r in self.db.execute(j_stmt).fetchall() if r[0]}

            active_emails = {p["email"] for p in active_faculty_profiles if p["email"]}
            journal_active_emails = journal_fac_emails.intersection(active_emails)
            faculty_with_journal_papers_but_no_patents = len(journal_active_emails - patent_filing_emails)

        # Departments with no patent / ipr contribution
        all_active_depts = {p.get("department") for p in active_faculty_profiles if p.get("department")}
        depts_with_patents = {r.get("department") for r in patent_rows if r.get("department")}
        depts_with_ipr = {r.get("department") for r in ipr_rows if r.get("department")}

        departments_with_no_patent_contribution = sorted(list(all_active_depts - depts_with_patents))
        departments_with_no_ipr_contribution = sorted(list(all_active_depts - depts_with_ipr))

        return {
            "total_valid_patents": total_valid_patents,
            "patent_filing_faculty": patent_filing_faculty,
            "total_active_faculty": total_active_faculty,
            "patents_granted": patents_granted,
            "patents_pending": patents_pending,
            "patent_grant_rate": patent_grant_rate,
            "total_ipr_records": total_ipr_records,
            "patents_per_active_faculty": patents_per_active,
            "patent_participation_rate": patent_participation_rate,
            "average_patent_score": average_patent_score,
            "average_validated_patent_score": average_validated_patent_score,
            "faculty_with_multiple_patents": faculty_with_multiple_patents,
            "faculty_with_journal_papers_but_no_patents": faculty_with_journal_papers_but_no_patents,
            "departments_with_no_patent_contribution": departments_with_no_patent_contribution,
            "departments_with_no_ipr_contribution": departments_with_no_ipr_contribution,
        }

    def status_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 2: GET /status"""
        patent_rows = self._get_filtered_patents(filters)
        ipr_rows = self._get_filtered_ipr(filters)

        total_patents = len(patent_rows)
        total_ipr = len(ipr_rows)

        p_status_counts: Dict[str, int] = {}
        granted_by_school: Dict[str, int] = {}
        for r in patent_rows:
            st = r["normalized_status"]
            p_status_counts[st] = p_status_counts.get(st, 0) + 1

            if st == "Granted":
                sch = r.get("school") or "Unassigned"
                granted_by_school[sch] = granted_by_school.get(sch, 0) + 1

        ipr_status_counts: Dict[str, int] = {}
        for r in ipr_rows:
            st = r["normalized_status"]
            ipr_status_counts[st] = ipr_status_counts.get(st, 0) + 1

        patent_status_distribution = [
            {"status": st, "count": cnt, "percentage": round((cnt / total_patents * 100.0), 2) if total_patents > 0 else 0.0}
            for st, cnt in sorted(p_status_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        ipr_status_distribution = [
            {"status": st, "count": cnt, "percentage": round((cnt / total_ipr * 100.0), 2) if total_ipr > 0 else 0.0}
            for st, cnt in sorted(ipr_status_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        total_granted = sum(granted_by_school.values())
        granted_patent_share_by_school = [
            {"school": sch, "granted_patents": cnt, "percentage": round((cnt / total_granted * 100.0), 2) if total_granted > 0 else 0.0}
            for sch, cnt in sorted(granted_by_school.items(), key=lambda x: x[1], reverse=True)
        ]

        missing_status_count = sum(1 for r in patent_rows + ipr_rows if r.get("normalized_status") == "Unknown")

        file_nos: Dict[str, int] = {}
        for r in patent_rows + ipr_rows:
            fn = str(r.get("file_no") or "").strip().lower()
            if fn:
                file_nos[fn] = file_nos.get(fn, 0) + 1
        duplicate_file_number_count = sum(1 for fn, cnt in file_nos.items() if cnt > 1)

        future_patent_date_count = sum(1 for r in patent_rows if "future_date" in r.get("flags", []))

        # Missing title count across raw tables
        patent_table, ipr_table, _, _ = self._get_tables()
        missing_title_count = 0
        if patent_table is not None:
            p_cols = SchemaReflector.column_names(patent_table)
            p_t = SchemaReflector.first_existing(p_cols, TITLE_COLUMNS) or "title"
            p_stmt = select(func.count()).where(or_(patent_table.c[p_t].is_(None), func.trim(patent_table.c[p_t]) == ""))
            missing_title_count += int(self.db.execute(p_stmt).scalar() or 0)

        if ipr_table is not None:
            i_cols = SchemaReflector.column_names(ipr_table)
            i_t = SchemaReflector.first_existing(i_cols, TITLE_COLUMNS) or "title"
            i_stmt = select(func.count()).where(or_(ipr_table.c[i_t].is_(None), func.trim(ipr_table.c[i_t]) == ""))
            missing_title_count += int(self.db.execute(i_stmt).scalar() or 0)

        # Unmatched faculty email count
        active_fac = self._get_active_faculty_profiles({})
        active_emails = {p["email"] for p in active_fac if p["email"]}

        unmatched_faculty_email_count = 0
        if patent_table is not None:
            p_cols = SchemaReflector.column_names(patent_table)
            p_e = SchemaReflector.first_existing(p_cols, EMAIL_COLUMNS) or "faculty_email"
            res = self.db.execute(select(distinct(func.lower(func.trim(patent_table.c[p_e]))))).fetchall()
            p_emails = {str(r[0]).lower().strip() for r in res if r[0]}
            unmatched_faculty_email_count += len(p_emails - active_emails)

        if ipr_table is not None:
            i_cols = SchemaReflector.column_names(ipr_table)
            i_e = SchemaReflector.first_existing(i_cols, EMAIL_COLUMNS) or "faculty_email"
            res = self.db.execute(select(distinct(func.lower(func.trim(ipr_table.c[i_e]))))).fetchall()
            i_emails = {str(r[0]).lower().strip() for r in res if r[0]}
            unmatched_faculty_email_count += len(i_emails - active_emails)

        return {
            "patent_status_distribution": patent_status_distribution,
            "ipr_status_distribution": ipr_status_distribution,
            "granted_patent_share_by_school": granted_patent_share_by_school,
            "missing_status_count": missing_status_count,
            "duplicate_file_number_count": duplicate_file_number_count,
            "future_patent_date_count": future_patent_date_count,
            "missing_title_count": missing_title_count,
            "unmatched_faculty_email_count": unmatched_faculty_email_count,
        }

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 3: GET /departments"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        dept_active_fac: Dict[Tuple[str, str], Set[str]] = {}
        for p in active_faculty_profiles:
            s = p.get("school") or "Unassigned"
            d = p.get("department") or "Unassigned"
            dept_active_fac.setdefault((s, d), set()).add(p["email"])

        patent_rows = self._get_filtered_patents(filters)
        ipr_rows = self._get_filtered_ipr(filters)

        dept_patents: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for r in patent_rows:
            s = r.get("school") or "Unassigned"
            d = r.get("department") or "Unassigned"
            dept_patents.setdefault((s, d), []).append(r)

        dept_ipr: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for r in ipr_rows:
            s = r.get("school") or "Unassigned"
            d = r.get("department") or "Unassigned"
            dept_ipr.setdefault((s, d), []).append(r)

        all_keys = set(dept_active_fac.keys()).union(dept_patents.keys()).union(dept_ipr.keys())

        dept_items = []
        for key in sorted(all_keys):
            school, department = key
            active_fac_count = len(dept_active_fac.get(key, set()))
            p_rows = dept_patents.get(key, [])
            i_rows = dept_ipr.get(key, [])

            total_valid_patents = len(p_rows)
            total_ipr_records = len(i_rows)

            filing_emails = {r["faculty_email"] for r in p_rows if r.get("faculty_email")}
            patent_filing_faculty = len(filing_emails)

            patent_part_rate = round((patent_filing_faculty / active_fac_count * 100.0), 2) if active_fac_count > 0 else 0.0
            patents_granted = sum(1 for r in p_rows if r.get("normalized_status") == "Granted")
            patents_pending = sum(1 for r in p_rows if r.get("normalized_status") in ("Pending", "Filed"))

            p_scores = [float(r.get("score") or 0.0) for r in p_rows]
            v_scores = [float(r.get("final_validated_score") or 0.0) for r in p_rows]

            avg_score = round(sum(p_scores) / len(p_scores), 2) if p_scores else 0.0
            avg_val_score = round(sum(v_scores) / len(v_scores), 2) if v_scores else 0.0

            dept_items.append({
                "school": school,
                "department": department,
                "active_faculty": active_fac_count,
                "total_valid_patents": total_valid_patents,
                "patent_filing_faculty": patent_filing_faculty,
                "patent_participation_rate": patent_part_rate,
                "patents_granted": patents_granted,
                "patents_pending": patents_pending,
                "total_ipr_records": total_ipr_records,
                "average_patent_score": avg_score,
                "average_validated_patent_score": avg_val_score,
            })

        # Sorting
        sort_by = filters.get("sort_by") or "total_valid_patents"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        if sort_by in ["total_valid_patents", "active_faculty", "patent_filing_faculty", "patent_participation_rate", "patents_granted", "patents_pending", "total_ipr_records", "average_patent_score", "average_validated_patent_score"]:
            dept_items.sort(key=lambda x: x.get(sort_by) or 0, reverse=reverse)
        else:
            dept_items.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_depts = len(dept_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = dept_items[start_idx:end_idx]

        return {
            "total": total_depts,
            "page": page,
            "page_size": page_size,
            "items": paginated_items,
        }

    def faculty(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 4: GET /faculty"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        active_email_map = {p["email"]: p for p in active_faculty_profiles if p["email"]}

        patent_rows = self._get_filtered_patents(filters)
        ipr_rows = self._get_filtered_ipr(filters)

        fac_patents: Dict[str, List[Dict[str, Any]]] = {}
        for r in patent_rows:
            fe = r.get("faculty_email")
            if fe:
                fac_patents.setdefault(fe, []).append(r)

        fac_ipr: Dict[str, List[Dict[str, Any]]] = {}
        for r in ipr_rows:
            fe = r.get("faculty_email")
            if fe:
                fac_ipr.setdefault(fe, []).append(r)

        all_emails = set(active_email_map.keys()).union(fac_patents.keys()).union(fac_ipr.keys())

        faculty_items = []
        for email in sorted(all_emails):
            prof = active_email_map.get(email, {})
            p_rows = fac_patents.get(email, [])
            i_rows = fac_ipr.get(email, [])

            name = prof.get("faculty_name") or (p_rows[0].get("faculty_name") if p_rows else (i_rows[0].get("faculty_name") if i_rows else "Unknown"))
            emp_id = prof.get("employee_id") or (p_rows[0].get("employee_id") if p_rows else (i_rows[0].get("employee_id") if i_rows else "N/A"))
            sch = prof.get("school") or (p_rows[0].get("school") if p_rows else (i_rows[0].get("school") if i_rows else "N/A"))
            dept = prof.get("department") or (p_rows[0].get("department") if p_rows else (i_rows[0].get("department") if i_rows else "N/A"))
            desig = prof.get("designation") or (p_rows[0].get("designation") if p_rows else (i_rows[0].get("designation") if i_rows else "N/A"))

            total_valid_patents = len(p_rows)
            total_ipr_records = len(i_rows)
            patents_granted = sum(1 for r in p_rows if r.get("normalized_status") == "Granted")
            patents_pending = sum(1 for r in p_rows if r.get("normalized_status") in ("Pending", "Filed"))

            scores = [float(r.get("score") or 0.0) for r in p_rows]
            val_scores = [float(r.get("final_validated_score") or 0.0) for r in p_rows]

            avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
            latest_val_score = round(val_scores[-1], 2) if val_scores else 0.0

            faculty_items.append({
                "faculty_name": name,
                "employee_id": emp_id,
                "school": sch,
                "department": dept,
                "designation": desig,
                "total_valid_patents": total_valid_patents,
                "patents_granted": patents_granted,
                "patents_pending": patents_pending,
                "total_ipr_records": total_ipr_records,
                "average_score": avg_score,
                "latest_validated_score": latest_val_score,
            })

        # Sorting
        sort_by = filters.get("sort_by") or "total_valid_patents"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        if sort_by in ["total_valid_patents", "patents_granted", "patents_pending", "total_ipr_records", "average_score", "latest_validated_score"]:
            faculty_items.sort(key=lambda x: x.get(sort_by) or 0, reverse=reverse)
        else:
            faculty_items.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_fac = len(faculty_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = faculty_items[start_idx:end_idx]

        return {
            "total": total_fac,
            "page": page,
            "page_size": page_size,
            "items": paginated_items,
        }

    def records_patents(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 5: GET /records/patents"""
        rows = self._get_filtered_patents(filters)

        sort_by = filters.get("sort_by") or "title"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        numeric_sort_fields = ["id", "score", "hod_score", "director_score", "dean_score", "vc_score", "final_validated_score"]

        if sort_by in numeric_sort_fields:
            rows.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            rows.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_recs = len(rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = rows[start_idx:end_idx]

        return {
            "total": total_recs,
            "page": page,
            "page_size": page_size,
            "items": paginated_items,
        }

    def records_ipr(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 6: GET /records/ipr"""
        rows = self._get_filtered_ipr(filters)

        sort_by = filters.get("sort_by") or "title"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        if sort_by in ["id", "score"]:
            rows.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            rows.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_recs = len(rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = rows[start_idx:end_idx]

        return {
            "total": total_recs,
            "page": page,
            "page_size": page_size,
            "items": paginated_items,
        }

    def trends(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 7: GET /trends"""
        patent_rows = self._get_filtered_patents(filters)
        ipr_rows = self._get_filtered_ipr(filters)

        patents_by_yr: Dict[str, Dict[str, int]] = {}
        for r in patent_rows:
            yr_num = parse_numeric_year(r.get("patent_date") or r.get("academic_year"))
            yr_str = str(yr_num) if yr_num else "Unspecified"
            patents_by_yr.setdefault(yr_str, {"total_patents": 0, "patents_granted": 0})
            patents_by_yr[yr_str]["total_patents"] += 1
            if r.get("normalized_status") == "Granted":
                patents_by_yr[yr_str]["patents_granted"] += 1

        ipr_by_yr: Dict[str, int] = {}
        for r in ipr_rows:
            yr_num = parse_numeric_year(r.get("ipr_date"))
            yr_str = str(yr_num) if yr_num else "Unspecified"
            ipr_by_yr[yr_str] = ipr_by_yr.get(yr_str, 0) + 1

        all_years = sorted(
            list(set(patents_by_yr.keys()).union(ipr_by_yr.keys())),
            key=lambda y: int(y) if y.isdigit() else 0
        )

        patents_by_year_list = [
            {
                "year": yr,
                "total_patents": patents_by_yr.get(yr, {}).get("total_patents", 0),
                "patents_granted": patents_by_yr.get(yr, {}).get("patents_granted", 0),
            }
            for yr in all_years if yr != "Unspecified"
        ]

        ipr_by_year_list = [
            {
                "year": yr,
                "total_ipr": ipr_by_yr.get(yr, 0),
            }
            for yr in all_years if yr != "Unspecified"
        ]

        yoy_growth_list = []
        for i, yr in enumerate(all_years):
            if not yr.isdigit():
                continue
            if i > 0 and all_years[i - 1].isdigit():
                prev_yr = all_years[i - 1]
                p_curr = patents_by_yr.get(yr, {}).get("total_patents", 0)
                p_prev = patents_by_yr.get(prev_yr, {}).get("total_patents", 0)
                p_growth = round(((p_curr - p_prev) / p_prev * 100.0), 2) if p_prev > 0 else (100.0 if p_curr > 0 else 0.0)

                i_curr = ipr_by_yr.get(yr, 0)
                i_prev = ipr_by_yr.get(prev_yr, 0)
                i_growth = round(((i_curr - i_prev) / i_prev * 100.0), 2) if i_prev > 0 else (100.0 if i_curr > 0 else 0.0)

                yoy_growth_list.append({
                    "year": yr,
                    "patent_growth_rate": p_growth,
                    "ipr_growth_rate": i_growth,
                })
            else:
                yoy_growth_list.append({
                    "year": yr,
                    "patent_growth_rate": 0.0,
                    "ipr_growth_rate": 0.0,
                })

        return {
            "patents_by_year": patents_by_year_list,
            "ipr_by_year": ipr_by_year_list,
            "patent_ipr_year_over_year_growth": yoy_growth_list,
        }

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Endpoint 8: GET /export"""
        patent_rows = self._get_filtered_patents(filters)
        ipr_rows = self._get_filtered_ipr(filters)

        export_rows = []
        for r in patent_rows:
            export_rows.append({
                "Record Type": "Patent",
                "ID": r.get("id"),
                "Faculty Email": r.get("faculty_email"),
                "Faculty Name": r.get("faculty_name"),
                "Employee ID": r.get("employee_id"),
                "Department": r.get("department"),
                "School": r.get("school"),
                "Title": r.get("title"),
                "Type": r.get("type"),
                "Scope": r.get("scope"),
                "Normalized Scope": r.get("normalized_scope"),
                "Date": r.get("patent_date"),
                "Status": r.get("patent_status"),
                "Normalized Status": r.get("normalized_status"),
                "File No": r.get("file_no"),
                "Academic Year": r.get("academic_year"),
                "Self Score": r.get("score"),
                "HOD Score": r.get("hod_score"),
                "Director Score": r.get("director_score"),
                "Dean Score": r.get("dean_score"),
                "VC Score": r.get("vc_score"),
                "Final Validated Score": r.get("final_validated_score"),
            })

        for r in ipr_rows:
            export_rows.append({
                "Record Type": "IPR",
                "ID": r.get("id"),
                "Faculty Email": r.get("faculty_email"),
                "Faculty Name": r.get("faculty_name"),
                "Employee ID": r.get("employee_id"),
                "Department": r.get("department"),
                "School": r.get("school"),
                "Title": r.get("title"),
                "Type": "IPR",
                "Scope": r.get("scope"),
                "Normalized Scope": r.get("normalized_scope"),
                "Date": r.get("ipr_date"),
                "Status": r.get("ipr_status"),
                "Normalized Status": r.get("normalized_status"),
                "File No": r.get("file_no"),
                "Academic Year": "N/A",
                "Self Score": r.get("score"),
                "HOD Score": 0.0,
                "Director Score": 0.0,
                "Dean Score": 0.0,
                "VC Score": 0.0,
                "Final Validated Score": r.get("score"),
            })

        return export_rows
