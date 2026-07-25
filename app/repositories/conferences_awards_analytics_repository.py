import re
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import Table, and_, case, distinct, func, or_, select, text
from sqlalchemy.orm import Session

from app.core.constants import (
    AGENCY_COLUMNS,
    DEPARTMENT_COLUMNS,
    EMAIL_COLUMNS,
    EMPLOYEE_COLUMNS,
    NAME_COLUMNS,
    SCHOOL_COLUMNS,
    TITLE_COLUMNS,
    YEAR_COLUMNS,
)
from app.models.schema_reflector import SchemaReflector


def parse_numeric_year(val: Any) -> Optional[int]:
    if val is None:
        return None
    s = str(val).strip()
    match = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if match:
        return int(match.group(1))
    return None


class ConferencesAwardsAnalyticsRepository:
    """Repository for Conferences and Awards Analytics using SQLAlchemy Core."""

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
        conf_table = self._logical_table(["conferences", "confrences"])
        award_table = self._logical_table(["awards"])
        journal_table = self._logical_table(["journal_publications", "journals"])
        faculty_table = self._logical_table(["faculty_profiles", "faculty", "users"])
        return conf_table, award_table, journal_table, faculty_table

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

        if filters.get("school") and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])
        if filters.get("department") and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])
        if filters.get("designation") and f_desig in faculty_table.c:
            clauses.append(faculty_table.c[f_desig] == filters["designation"])
        if filters.get("faculty"):
            target_fac = str(filters["faculty"]).lower().strip()
            clauses.append(
                or_(
                    func.lower(func.trim(faculty_table.c[f_email])) == target_fac,
                    func.lower(faculty_table.c[f_name]).like(f"%{target_fac}%"),
                )
            )

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

    def _get_journal_publication_counts(self) -> Tuple[Dict[str, int], Dict[str, List[int]]]:
        _, _, journal_table, _ = self._get_tables()
        if journal_table is None:
            return {}, {}

        j_cols = SchemaReflector.column_names(journal_table)
        j_email = SchemaReflector.first_existing(j_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        j_title = SchemaReflector.first_existing(j_cols, TITLE_COLUMNS) or "title"
        j_year = SchemaReflector.first_existing(j_cols, YEAR_COLUMNS) or "publication_year"

        stmt = select(
            journal_table.c[j_email].label("email"),
            journal_table.c[j_year].label("academic_year") if j_year in journal_table.c else text("''").label("academic_year"),
        )
        if j_title in journal_table.c:
            stmt = stmt.where(and_(journal_table.c[j_title].isnot(None), func.trim(journal_table.c[j_title]) != ""))

        res = self.db.execute(stmt).fetchall()

        counts: Dict[str, int] = {}
        years_map: Dict[str, List[int]] = {}
        for r in res:
            em = str(r[0] or "").lower().strip()
            if em:
                counts[em] = counts.get(em, 0) + 1
                yr_num = parse_numeric_year(r[1])
                if yr_num:
                    years_map.setdefault(em, []).append(yr_num)

        return counts, years_map

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        conf_table, award_table, _, faculty_table = self._get_tables()
        if faculty_table is None:
            return {
                "conferences": [],
                "awards": [],
                "summary": {},
                "department_comparison": [],
                "faculty_details": [],
            }

        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        active_email_map = {p["email"]: p for p in active_faculty_profiles if p["email"]}

        journal_counts, journal_years = self._get_journal_publication_counts()

        f_cols = SchemaReflector.column_names(faculty_table)
        f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
        f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
        f_emp = SchemaReflector.first_existing(f_cols, EMPLOYEE_COLUMNS) or "employee_id"
        f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
        f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"
        f_desig = SchemaReflector.first_existing(f_cols, ["designation", "role"]) or "designation"

        # 1. Fetch Conferences
        conf_records = []
        if conf_table is not None:
            c_cols = SchemaReflector.column_names(conf_table)
            c_id = SchemaReflector.first_existing(c_cols, ["id", "conference_id"]) or "id"
            c_email = SchemaReflector.first_existing(c_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
            c_title = SchemaReflector.first_existing(c_cols, TITLE_COLUMNS) or "title"
            c_type = SchemaReflector.first_existing(c_cols, ["type", "presentation_type"]) or "type"
            c_org = SchemaReflector.first_existing(c_cols, ["organisation", "organization", "organizer", "organising_institution"]) or "organisation"
            c_level = SchemaReflector.first_existing(c_cols, ["level", "conference_level"]) or "level"
            c_year = SchemaReflector.first_existing(c_cols, YEAR_COLUMNS) or "academic_year"
            c_score = SchemaReflector.first_existing(c_cols, ["score", "self_score"]) or "score"
            c_hod = SchemaReflector.first_existing(c_cols, ["hod_score"]) or "hod_score"
            c_dir = SchemaReflector.first_existing(c_cols, ["director_score"]) or "director_score"
            c_dean = SchemaReflector.first_existing(c_cols, ["dean_score"]) or "dean_score"
            c_vc = SchemaReflector.first_existing(c_cols, ["vc_score", "vc_approved_score", "final_score"]) or "vc_score"

            select_fields = [
                conf_table.c[c_id].label("id") if c_id in conf_table.c else conf_table.c[c_cols[0]].label("id"),
                conf_table.c[c_email].label("c_faculty_email") if c_email in conf_table.c else text("''").label("c_faculty_email"),
                conf_table.c[c_title].label("title") if c_title in conf_table.c else text("''").label("title"),
                conf_table.c[c_type].label("type") if c_type in conf_table.c else text("''").label("type"),
                conf_table.c[c_org].label("organisation") if c_org in conf_table.c else text("''").label("organisation"),
                conf_table.c[c_level].label("level") if c_level in conf_table.c else text("''").label("level"),
                conf_table.c[c_year].label("academic_year") if c_year in conf_table.c else text("''").label("academic_year"),
                conf_table.c[c_score].label("score") if c_score in conf_table.c else text("0.0").label("score"),
                conf_table.c[c_hod].label("hod_score") if c_hod in conf_table.c else text("0.0").label("hod_score"),
                conf_table.c[c_dir].label("director_score") if c_dir in conf_table.c else text("0.0").label("director_score"),
                conf_table.c[c_dean].label("dean_score") if c_dean in conf_table.c else text("0.0").label("dean_score"),
                conf_table.c[c_vc].label("vc_score") if c_vc in conf_table.c else text("0.0").label("vc_score"),
                faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else text("''").label("f_email"),
                faculty_table.c[f_name].label("full_name") if f_name in faculty_table.c else text("''").label("full_name"),
                faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else text("''").label("department"),
                faculty_table.c[f_school].label("school") if f_school in faculty_table.c else text("''").label("school"),
            ]

            stmt = select(*select_fields)
            c_email_col = conf_table.c[c_email] if c_email in conf_table.c else conf_table.c[c_cols[0]]
            f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]

            join_clause = func.lower(func.trim(c_email_col)) == func.lower(func.trim(f_email_col))
            stmt = stmt.select_from(conf_table.join(faculty_table, join_clause))

            clauses = []
            if "is_active" in faculty_table.c:
                clauses.append(faculty_table.c.is_active == True)

            if filters.get("academic_year") and c_year in conf_table.c:
                clauses.append(func.cast(conf_table.c[c_year], text("VARCHAR")) == str(filters["academic_year"]))
            if filters.get("school") and f_school in faculty_table.c:
                clauses.append(faculty_table.c[f_school] == filters["school"])
            if filters.get("department") and f_dept in faculty_table.c:
                clauses.append(faculty_table.c[f_dept] == filters["department"])
            if filters.get("designation") and f_desig in faculty_table.c:
                clauses.append(faculty_table.c[f_desig] == filters["designation"])
            if filters.get("faculty"):
                target_fac = str(filters["faculty"]).lower().strip()
                clauses.append(
                    or_(
                        func.lower(func.trim(f_email_col)) == target_fac,
                        func.lower(faculty_table.c[f_name]).like(f"%{target_fac}%"),
                    )
                )

            if clauses:
                stmt = stmt.where(and_(*clauses))

            res = self.db.execute(stmt).fetchall()
            for r in res:
                rd = dict(r._mapping)
                em = str(rd.get("f_email") or rd.get("c_faculty_email") or "").lower().strip()
                rd["faculty_email"] = em
                rd["organization"] = rd.get("organisation") or ""
                rd["journal_publications"] = journal_counts.get(em, 0)
                rd["score"] = float(rd.get("score") or 0.0)
                rd["hod_score"] = float(rd.get("hod_score") or 0.0)
                rd["director_score"] = float(rd.get("director_score") or 0.0)
                rd["dean_score"] = float(rd.get("dean_score") or 0.0)
                rd["vc_score"] = float(rd.get("vc_score") or 0.0)
                conf_records.append(rd)

        # 2. Fetch Awards
        award_records = []
        if award_table is not None:
            a_cols = SchemaReflector.column_names(award_table)
            a_id = SchemaReflector.first_existing(a_cols, ["id", "award_id"]) or "id"
            a_email = SchemaReflector.first_existing(a_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
            a_title = SchemaReflector.first_existing(a_cols, TITLE_COLUMNS) or "title"
            a_date = SchemaReflector.first_existing(a_cols, ["award_date", "date", "conferred_date"]) or "award_date"
            a_agency = SchemaReflector.first_existing(a_cols, AGENCY_COLUMNS) or "agency"
            a_level = SchemaReflector.first_existing(a_cols, ["level", "award_level"]) or "level"
            a_year = SchemaReflector.first_existing(a_cols, YEAR_COLUMNS) or "academic_year"
            a_score = SchemaReflector.first_existing(a_cols, ["score", "self_score"]) or "score"
            a_hod = SchemaReflector.first_existing(a_cols, ["hod_score"]) or "hod_score"
            a_dir = SchemaReflector.first_existing(a_cols, ["director_score"]) or "director_score"
            a_dean = SchemaReflector.first_existing(a_cols, ["dean_score"]) or "dean_score"
            a_vc = SchemaReflector.first_existing(a_cols, ["vc_score", "vc_approved_score", "final_score"]) or "vc_score"

            select_fields = [
                award_table.c[a_id].label("id") if a_id in award_table.c else award_table.c[a_cols[0]].label("id"),
                award_table.c[a_email].label("a_faculty_email") if a_email in award_table.c else text("''").label("a_faculty_email"),
                award_table.c[a_title].label("title") if a_title in award_table.c else text("''").label("title"),
                award_table.c[a_date].label("award_date") if a_date in award_table.c else text("NULL").label("award_date"),
                award_table.c[a_agency].label("agency") if a_agency in award_table.c else text("''").label("agency"),
                award_table.c[a_level].label("level") if a_level in award_table.c else text("''").label("level"),
                award_table.c[a_year].label("academic_year") if a_year in award_table.c else text("''").label("academic_year"),
                award_table.c[a_score].label("score") if a_score in award_table.c else text("0.0").label("score"),
                award_table.c[a_hod].label("hod_score") if a_hod in award_table.c else text("0.0").label("hod_score"),
                award_table.c[a_dir].label("director_score") if a_dir in award_table.c else text("0.0").label("director_score"),
                award_table.c[a_dean].label("dean_score") if a_dean in award_table.c else text("0.0").label("dean_score"),
                award_table.c[a_vc].label("vc_score") if a_vc in award_table.c else text("0.0").label("vc_score"),
                faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else text("''").label("f_email"),
                faculty_table.c[f_name].label("full_name") if f_name in faculty_table.c else text("''").label("full_name"),
                faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else text("''").label("department"),
                faculty_table.c[f_school].label("school") if f_school in faculty_table.c else text("''").label("school"),
            ]

            stmt = select(*select_fields)
            a_email_col = award_table.c[a_email] if a_email in award_table.c else award_table.c[a_cols[0]]
            f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]

            join_clause = func.lower(func.trim(a_email_col)) == func.lower(func.trim(f_email_col))
            stmt = stmt.select_from(award_table.join(faculty_table, join_clause))

            clauses = []
            if "is_active" in faculty_table.c:
                clauses.append(faculty_table.c.is_active == True)

            if filters.get("academic_year") and a_year in award_table.c:
                clauses.append(func.cast(award_table.c[a_year], text("VARCHAR")) == str(filters["academic_year"]))
            if filters.get("school") and f_school in faculty_table.c:
                clauses.append(faculty_table.c[f_school] == filters["school"])
            if filters.get("department") and f_dept in faculty_table.c:
                clauses.append(faculty_table.c[f_dept] == filters["department"])
            if filters.get("designation") and f_desig in faculty_table.c:
                clauses.append(faculty_table.c[f_desig] == filters["designation"])
            if filters.get("faculty"):
                target_fac = str(filters["faculty"]).lower().strip()
                clauses.append(
                    or_(
                        func.lower(func.trim(f_email_col)) == target_fac,
                        func.lower(faculty_table.c[f_name]).like(f"%{target_fac}%"),
                    )
                )

            if clauses:
                stmt = stmt.where(and_(*clauses))

            res = self.db.execute(stmt).fetchall()
            for r in res:
                rd = dict(r._mapping)
                em = str(rd.get("f_email") or rd.get("a_faculty_email") or "").lower().strip()
                rd["faculty_email"] = em
                rd["journal_publications"] = journal_counts.get(em, 0)
                rd["score"] = float(rd.get("score") or 0.0)
                rd["hod_score"] = float(rd.get("hod_score") or 0.0)
                rd["director_score"] = float(rd.get("director_score") or 0.0)
                rd["dean_score"] = float(rd.get("dean_score") or 0.0)
                rd["vc_score"] = float(rd.get("vc_score") or 0.0)
                award_records.append(rd)

        # Apply page_size limiting if specified
        page_size = filters.get("page_size")
        limited_conf_records = conf_records[:page_size] if page_size and page_size > 0 else conf_records
        limited_award_records = award_records[:page_size] if page_size and page_size > 0 else award_records

        # Summary Metrics Computation
        total_active_fac = len({p["email"] for p in active_faculty_profiles if p["email"]})
        conf_fac_emails = {r["faculty_email"] for r in conf_records if r.get("faculty_email")}
        award_fac_emails = {r["faculty_email"] for r in award_records if r.get("faculty_email")}

        total_conferences = len(conf_records)
        conf_part_fac = len(conf_fac_emails)
        conf_part_rate = round((conf_part_fac / total_active_fac * 100.0), 2) if total_active_fac > 0 else 0.0

        total_awards = len(award_records)
        award_fac_count = len(award_fac_emails)

        intl_count = 0
        for r in conf_records:
            lvl = str(r.get("level") or "").lower()
            if "international" in lvl or "global" in lvl:
                intl_count += 1
        for r in award_records:
            lvl = str(r.get("level") or "").lower()
            if "international" in lvl or "global" in lvl:
                intl_count += 1

        # Breakdowns
        conf_by_dept: Dict[str, int] = {}
        conf_by_sch: Dict[str, int] = {}
        conf_by_yr: Dict[str, int] = {}
        conf_by_type: Dict[str, int] = {}
        conf_by_level: Dict[str, int] = {}
        top_orgs: Dict[str, int] = {}
        conf_scores: List[float] = []

        nat_vs_intl = {"national": 0, "international": 0, "other": 0}

        fac_conf_counts: Dict[str, int] = {}

        for r in conf_records:
            d = str(r.get("department") or "Unassigned")
            conf_by_dept[d] = conf_by_dept.get(d, 0) + 1

            s = str(r.get("school") or "Unassigned")
            conf_by_sch[s] = conf_by_sch.get(s, 0) + 1

            yr = str(r.get("academic_year") or "Unspecified")
            conf_by_yr[yr] = conf_by_yr.get(yr, 0) + 1

            t = str(r.get("type") or "Unspecified")
            conf_by_type[t] = conf_by_type.get(t, 0) + 1

            lvl = str(r.get("level") or "Unspecified")
            conf_by_level[lvl] = conf_by_level.get(lvl, 0) + 1

            lvl_lower = lvl.lower()
            if "international" in lvl_lower or "global" in lvl_lower:
                nat_vs_intl["international"] += 1
            elif "national" in lvl_lower or "domestic" in lvl_lower:
                nat_vs_intl["national"] += 1
            else:
                nat_vs_intl["other"] += 1

            org = str(r.get("organisation") or r.get("organization") or "Unspecified").strip()
            if org and org.lower() not in ("unspecified", "none", "n/a"):
                top_orgs[org] = top_orgs.get(org, 0) + 1

            conf_scores.append(float(r.get("score") or 0.0))

            fe = r.get("faculty_email")
            if fe:
                fac_conf_counts[fe] = fac_conf_counts.get(fe, 0) + 1

        award_by_dept: Dict[str, int] = {}
        award_by_sch: Dict[str, int] = {}
        award_by_level: Dict[str, int] = {}
        award_by_agency: Dict[str, int] = {}
        award_by_yr: Dict[str, int] = {}
        award_scores: List[float] = []
        fac_award_counts: Dict[str, int] = {}
        fac_award_names: Dict[str, Tuple[str, str]] = {}

        for r in award_records:
            d = str(r.get("department") or "Unassigned")
            award_by_dept[d] = award_by_dept.get(d, 0) + 1

            s = str(r.get("school") or "Unassigned")
            award_by_sch[s] = award_by_sch.get(s, 0) + 1

            lvl = str(r.get("level") or "Unspecified")
            award_by_level[lvl] = award_by_level.get(lvl, 0) + 1

            ag = str(r.get("agency") or "Unspecified")
            award_by_agency[ag] = award_by_agency.get(ag, 0) + 1

            yr = str(r.get("academic_year") or "Unspecified")
            award_by_yr[yr] = award_by_yr.get(yr, 0) + 1

            award_scores.append(float(r.get("score") or 0.0))

            fe = r.get("faculty_email")
            if fe:
                fac_award_counts[fe] = fac_award_counts.get(fe, 0) + 1
                fac_award_names[fe] = (r.get("full_name") or "Unknown", d)

        avg_conf_score = round(sum(conf_scores) / len(conf_scores), 2) if conf_scores else 0.0
        avg_award_score = round(sum(award_scores) / len(award_scores), 2) if award_scores else 0.0

        fac_multiple_conf = sum(1 for cnt in fac_conf_counts.values() if cnt >= 2)

        top_award_faculty = [
            {"faculty_name": fac_award_names.get(fe, ("Unknown", "Unassigned"))[0], "department": fac_award_names.get(fe, ("Unknown", "Unassigned"))[1], "award_count": cnt}
            for fe, cnt in sorted(fac_award_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Departments with high conference participation but low publications
        dept_active_fac: Dict[str, Set[str]] = {}
        for p in active_faculty_profiles:
            d = p.get("department") or "Unassigned"
            dept_active_fac.setdefault(d, set()).add(p["email"])

        dept_conf_fac: Dict[str, Set[str]] = {}
        for r in conf_records:
            d = r.get("department") or "Unassigned"
            if r.get("faculty_email"):
                dept_conf_fac.setdefault(d, set()).add(r["faculty_email"])

        dept_pubs: Dict[str, int] = {}
        for em, cnt in journal_counts.items():
            prof = active_email_map.get(em)
            if prof:
                d = prof.get("department") or "Unassigned"
                dept_pubs[d] = dept_pubs.get(d, 0) + cnt

        all_depts = set(dept_active_fac.keys())
        dept_metrics = []
        total_conf_part = 0
        total_active = 0
        total_pub_cnt = 0

        for d in all_depts:
            act_fac_cnt = len(dept_active_fac.get(d, set()))
            c_fac_cnt = len(dept_conf_fac.get(d, set()))
            p_cnt = dept_pubs.get(d, 0)

            c_rate = (c_fac_cnt / act_fac_cnt * 100.0) if act_fac_cnt > 0 else 0.0
            avg_pubs = (p_cnt / act_fac_cnt) if act_fac_cnt > 0 else 0.0

            total_conf_part += c_fac_cnt
            total_active += act_fac_cnt
            total_pub_cnt += p_cnt

            dept_metrics.append({"department": d, "c_rate": c_rate, "avg_pubs": avg_pubs})

        overall_avg_c_rate = (total_conf_part / total_active * 100.0) if total_active > 0 else 0.0
        overall_avg_pubs = (total_pub_cnt / total_active) if total_active > 0 else 0.0

        high_conf_low_pub_depts = [
            m["department"] for m in dept_metrics
            if m["c_rate"] > overall_avg_c_rate and m["avg_pubs"] < overall_avg_pubs
        ]

        # Faculty receiving awards after recorded research contributions
        fac_awards_after_research = []
        for r in award_records:
            fe = r.get("faculty_email")
            if fe and fe in journal_years:
                award_yr = parse_numeric_year(r.get("academic_year") or r.get("award_date"))
                pub_yrs = journal_years[fe]
                if award_yr is not None and pub_yrs:
                    min_pub_yr = min(pub_yrs)
                    if min_pub_yr <= award_yr:
                        fname = r.get("full_name") or fe
                        if fname not in fac_awards_after_research:
                            fac_awards_after_research.append(fname)

        summary = {
            "total_conferences": total_conferences,
            "conference_participating_faculty": conf_part_fac,
            "conference_participation_rate": conf_part_rate,
            "total_awards": total_awards,
            "award_receiving_faculty": award_fac_count,
            "international_level_activities": intl_count,
            "conferences_by_department": [{"department": k, "count": v} for k, v in sorted(conf_by_dept.items(), key=lambda x: x[1], reverse=True)],
            "conferences_by_school": [{"school": k, "count": v} for k, v in sorted(conf_by_sch.items(), key=lambda x: x[1], reverse=True)],
            "conferences_by_academic_year": [{"academic_year": k, "count": v} for k, v in sorted(conf_by_yr.items())],
            "conferences_by_type": [{"type": k, "count": v} for k, v in sorted(conf_by_type.items(), key=lambda x: x[1], reverse=True)],
            "conferences_by_level": [{"level": k, "count": v} for k, v in sorted(conf_by_level.items(), key=lambda x: x[1], reverse=True)],
            "national_versus_international_participation": nat_vs_intl,
            "top_organising_institutions": [{"organisation": k, "count": v} for k, v in sorted(top_orgs.items(), key=lambda x: x[1], reverse=True)[:10]],
            "awards_by_department": [{"department": k, "count": v} for k, v in sorted(award_by_dept.items(), key=lambda x: x[1], reverse=True)],
            "awards_by_school": [{"school": k, "count": v} for k, v in sorted(award_by_sch.items(), key=lambda x: x[1], reverse=True)],
            "awards_by_level": [{"level": k, "count": v} for k, v in sorted(award_by_level.items(), key=lambda x: x[1], reverse=True)],
            "awards_by_agency": [{"agency": k, "count": v} for k, v in sorted(award_by_agency.items(), key=lambda x: x[1], reverse=True)],
            "awards_by_academic_year": [{"academic_year": k, "count": v} for k, v in sorted(award_by_yr.items())],
            "top_award_receiving_faculty": top_award_faculty,
            "average_conference_score": avg_conf_score,
            "average_award_score": avg_award_score,
            "faculty_with_multiple_conference_activities": fac_multiple_conf,
            "departments_with_high_conference_participation_but_low_publications": sorted(high_conf_low_pub_depts),
            "faculty_receiving_awards_after_recorded_research_contributions": sorted(fac_awards_after_research),
        }

        # 3. Department Comparison List
        dept_sch_map: Dict[Tuple[str, str], List[str]] = {}
        for p in active_faculty_profiles:
            s = p.get("school") or "Unassigned"
            d = p.get("department") or "Unassigned"
            dept_sch_map.setdefault((s, d), []).append(p["email"])

        dept_comp_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for key, emails in dept_sch_map.items():
            sch, dept = key
            act_cnt = len(emails)
            dept_comp_map[key] = {
                "school": sch,
                "department": dept,
                "active_faculty": act_cnt,
                "total_conferences": 0,
                "conf_fac_set": set(),
                "total_awards": 0,
                "award_fac_set": set(),
                "total_journal_publications": sum(journal_counts.get(em, 0) for em in emails),
                "conf_scores": [],
                "award_scores": [],
            }

        for r in conf_records:
            sch = r.get("school") or "Unassigned"
            dept = r.get("department") or "Unassigned"
            key = (sch, dept)
            if key not in dept_comp_map:
                dept_comp_map[key] = {
                    "school": sch,
                    "department": dept,
                    "active_faculty": 0,
                    "total_conferences": 0,
                    "conf_fac_set": set(),
                    "total_awards": 0,
                    "award_fac_set": set(),
                    "total_journal_publications": 0,
                    "conf_scores": [],
                    "award_scores": [],
                }
            dept_comp_map[key]["total_conferences"] += 1
            if r.get("faculty_email"):
                dept_comp_map[key]["conf_fac_set"].add(r["faculty_email"])
            dept_comp_map[key]["conf_scores"].append(float(r.get("score") or 0.0))

        for r in award_records:
            sch = r.get("school") or "Unassigned"
            dept = r.get("department") or "Unassigned"
            key = (sch, dept)
            if key not in dept_comp_map:
                dept_comp_map[key] = {
                    "school": sch,
                    "department": dept,
                    "active_faculty": 0,
                    "total_conferences": 0,
                    "conf_fac_set": set(),
                    "total_awards": 0,
                    "award_fac_set": set(),
                    "total_journal_publications": 0,
                    "conf_scores": [],
                    "award_scores": [],
                }
            dept_comp_map[key]["total_awards"] += 1
            if r.get("faculty_email"):
                dept_comp_map[key]["award_fac_set"].add(r["faculty_email"])
            dept_comp_map[key]["award_scores"].append(float(r.get("score") or 0.0))

        department_comparison = []
        for key, data in sorted(dept_comp_map.items()):
            c_scores = data["conf_scores"]
            a_scores = data["award_scores"]
            avg_c = round(sum(c_scores) / len(c_scores), 2) if c_scores else 0.0
            avg_a = round(sum(a_scores) / len(a_scores), 2) if a_scores else 0.0

            department_comparison.append({
                "school": data["school"],
                "department": data["department"],
                "active_faculty": data["active_faculty"],
                "total_conferences": data["total_conferences"],
                "conference_participating_faculty": len(data["conf_fac_set"]),
                "total_awards": data["total_awards"],
                "award_receiving_faculty": len(data["award_fac_set"]),
                "total_journal_publications": data["total_journal_publications"],
                "average_conference_score": avg_c,
                "average_award_score": avg_a,
            })

        # 4. Faculty Details List
        fac_comp_map: Dict[str, Dict[str, Any]] = {}
        for email, p in active_email_map.items():
            fac_comp_map[email] = {
                "faculty_email": email,
                "full_name": p.get("faculty_name") or "Unknown",
                "department": p.get("department") or "N/A",
                "school": p.get("school") or "N/A",
                "designation": p.get("designation") or "N/A",
                "conference_count": 0,
                "award_count": 0,
                "journal_publication_count": journal_counts.get(email, 0),
                "conf_scores": [],
                "award_scores": [],
            }

        for r in conf_records:
            em = r.get("faculty_email")
            if em:
                if em not in fac_comp_map:
                    fac_comp_map[em] = {
                        "faculty_email": em,
                        "full_name": r.get("full_name") or "Unknown",
                        "department": r.get("department") or "N/A",
                        "school": r.get("school") or "N/A",
                        "designation": "N/A",
                        "conference_count": 0,
                        "award_count": 0,
                        "journal_publication_count": journal_counts.get(em, 0),
                        "conf_scores": [],
                        "award_scores": [],
                    }
                fac_comp_map[em]["conference_count"] += 1
                fac_comp_map[em]["conf_scores"].append(float(r.get("score") or 0.0))

        for r in award_records:
            em = r.get("faculty_email")
            if em:
                if em not in fac_comp_map:
                    fac_comp_map[em] = {
                        "faculty_email": em,
                        "full_name": r.get("full_name") or "Unknown",
                        "department": r.get("department") or "N/A",
                        "school": r.get("school") or "N/A",
                        "designation": "N/A",
                        "conference_count": 0,
                        "award_count": 0,
                        "journal_publication_count": journal_counts.get(em, 0),
                        "conf_scores": [],
                        "award_scores": [],
                    }
                fac_comp_map[em]["award_count"] += 1
                fac_comp_map[em]["award_scores"].append(float(r.get("score") or 0.0))

        faculty_details = []
        for em, data in sorted(fac_comp_map.items()):
            c_scores = data["conf_scores"]
            a_scores = data["award_scores"]
            avg_c = round(sum(c_scores) / len(c_scores), 2) if c_scores else 0.0
            avg_a = round(sum(a_scores) / len(a_scores), 2) if a_scores else 0.0

            faculty_details.append({
                "faculty_email": data["faculty_email"],
                "full_name": data["full_name"],
                "department": data["department"],
                "school": data["school"],
                "designation": data["designation"],
                "conference_count": data["conference_count"],
                "award_count": data["award_count"],
                "journal_publication_count": data["journal_publication_count"],
                "average_conference_score": avg_c,
                "average_award_score": avg_a,
            })

        return {
            "conferences": limited_conf_records,
            "awards": limited_award_records,
            "summary": summary,
            "department_comparison": department_comparison,
            "faculty_details": faculty_details,
        }
