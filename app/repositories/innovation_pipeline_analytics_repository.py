import re
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import Table, and_, case, distinct, func, literal, literal_column, or_, select, text
from sqlalchemy.orm import Session

from app.core.constants import (
    AGENCY_COLUMNS,
    AMOUNT_COLUMNS,
    DEPARTMENT_COLUMNS,
    EMAIL_COLUMNS,
    EMPLOYEE_COLUMNS,
    NAME_COLUMNS,
    SCHOOL_COLUMNS,
    STATUS_COLUMNS,
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


class InnovationPipelineAnalyticsRepository:
    """Repository for Innovation Pipeline Analytics using SQLAlchemy Core."""

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

    def _get_tables(self) -> Dict[str, Optional[Table]]:
        return {
            "proposals": self._logical_table(["research_proposals", "proposals"]),
            "internal_projects": self._logical_table(["research_projects", "internal_research_projects"]),
            "external_projects": self._logical_table(["external_research_projects", "external_projects"]),
            "patents": self._logical_table(["patents"]),
            "ipr": self._logical_table(["ipr_records"]),
            "products": self._logical_table(["products_developed", "products"]),
            "faculty": self._logical_table(["faculty_profiles", "faculty", "users"]),
        }

    def _get_active_faculty_profiles(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            tables = self._get_tables()
            faculty_table = tables["faculty"]
            if faculty_table is None:
                return []

            f_cols = SchemaReflector.column_names(faculty_table)
            if not f_cols:
                return []
            f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
            f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
            f_emp = SchemaReflector.first_existing(f_cols, EMPLOYEE_COLUMNS) or "employee_id"
            f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
            f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"
            f_desig = SchemaReflector.first_existing(f_cols, ["designation", "role"]) or "designation"

            select_fields = [
                faculty_table.c[f_email].label("email") if f_email and f_email in faculty_table.c else literal("").label("email"),
                faculty_table.c[f_name].label("faculty_name") if f_name and f_name in faculty_table.c else literal("").label("faculty_name"),
                faculty_table.c[f_emp].label("employee_id") if f_emp and f_emp in faculty_table.c else literal("").label("employee_id"),
                faculty_table.c[f_dept].label("department") if f_dept and f_dept in faculty_table.c else literal("").label("department"),
                faculty_table.c[f_school].label("school") if f_school and f_school in faculty_table.c else literal("").label("school"),
                faculty_table.c[f_desig].label("designation") if f_desig and f_desig in faculty_table.c else literal("").label("designation"),
            ]

            if "is_active" in faculty_table.c:
                select_fields.append(faculty_table.c.is_active.label("is_active"))
            else:
                select_fields.append(literal(1).label("is_active"))

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
            if filters.get("faculty") and f_email in faculty_table.c:
                target_fac = str(filters["faculty"]).lower().strip()
                clauses.append(
                    or_(
                        func.lower(func.trim(faculty_table.c[f_email])) == target_fac,
                        func.lower(faculty_table.c[f_name]).like(f"%{target_fac}%") if f_name in faculty_table.c else literal(False),
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
        except Exception:
            return []

    def _get_records_from_table(self, table: Optional[Table], category: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        if table is None:
            return []
        try:
            tables = self._get_tables()
            faculty_table = tables["faculty"]
            if faculty_table is None:
                return []

            cols = SchemaReflector.column_names(table)
            f_cols = SchemaReflector.column_names(faculty_table)
            if not cols or not f_cols:
                return []

            id_col = SchemaReflector.first_existing(cols, ["id", f"{category}_id"]) or (cols[0] if cols else None)
            email_col = SchemaReflector.first_existing(cols, ["faculty_email", "email", "official_email"]) or (cols[0] if cols else None)
            title_col = SchemaReflector.first_existing(cols, TITLE_COLUMNS) or "title"
            status_col = SchemaReflector.first_existing(cols, ["patent_status", "ipr_status", "project_status", "status"]) or "status"

            year_col = SchemaReflector.first_existing(cols, YEAR_COLUMNS) or "academic_year"
            amount_col = SchemaReflector.first_existing(cols, AMOUNT_COLUMNS) or "amount"
            score_col = SchemaReflector.first_existing(cols, ["score", "self_score"]) or "score"

            f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or (f_cols[0] if f_cols else None)
            f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
            f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
            f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"
            f_desig = SchemaReflector.first_existing(f_cols, ["designation", "role"]) or "designation"

            select_fields = [
                table.c[id_col].label("id") if id_col and id_col in table.c else literal(1).label("id"),
                table.c[email_col].label("t_email") if email_col and email_col in table.c else literal("").label("t_email"),
                table.c[title_col].label("title") if title_col and title_col in table.c else literal("").label("title"),
                table.c[status_col].label("status") if status_col and status_col in table.c else literal("").label("status"),
                table.c[year_col].label("academic_year") if year_col and year_col in table.c else literal("").label("academic_year"),
                table.c[amount_col].label("amount") if amount_col and amount_col in table.c else literal(0.0).label("amount"),
                table.c[score_col].label("score") if score_col and score_col in table.c else literal(0.0).label("score"),
                faculty_table.c[f_email].label("f_email") if f_email and f_email in faculty_table.c else literal("").label("f_email"),
                faculty_table.c[f_name].label("full_name") if f_name and f_name in faculty_table.c else literal("").label("full_name"),
                faculty_table.c[f_dept].label("department") if f_dept and f_dept in faculty_table.c else literal("").label("department"),
                faculty_table.c[f_school].label("school") if f_school and f_school in faculty_table.c else literal("").label("school"),
                faculty_table.c[f_desig].label("designation") if f_desig and f_desig in faculty_table.c else literal("").label("designation"),
            ]

            if category == "patent":
                p_date = SchemaReflector.first_existing(cols, ["patent_date", "date", "filing_date"]) or "patent_date"
                p_file = SchemaReflector.first_existing(cols, ["file_no", "application_no", "file_number"]) or "file_number"
                select_fields.append(table.c[p_date].label("patent_date") if p_date in table.c else literal_column("NULL").label("patent_date"))
                select_fields.append(table.c[p_file].label("file_number") if p_file in table.c else literal("").label("file_number"))
            elif category == "ipr":
                i_date = SchemaReflector.first_existing(cols, ["ipr_date", "date", "registration_date"]) or "ipr_date"
                i_file = SchemaReflector.first_existing(cols, ["file_no", "application_no", "file_number"]) or "file_number"
                select_fields.append(table.c[i_date].label("ipr_date") if i_date in table.c else literal_column("NULL").label("ipr_date"))
                select_fields.append(table.c[i_file].label("file_number") if i_file in table.c else literal("").label("file_number"))
            elif category in ("internal_project", "external_project"):
                s_date = SchemaReflector.first_existing(cols, ["sanction_date", "date", "start_date"]) or "sanction_date"
                agency_col = SchemaReflector.first_existing(cols, AGENCY_COLUMNS) or "agency"
                role_col = SchemaReflector.first_existing(cols, ["role", "investigator_role"]) or "role"
                select_fields.append(table.c[s_date].label("sanction_date") if s_date in table.c else literal_column("NULL").label("sanction_date"))
                select_fields.append(table.c[agency_col].label("agency") if agency_col in table.c else literal("").label("agency"))
                select_fields.append(table.c[role_col].label("role") if role_col in table.c else literal("").label("role"))
            elif category == "product":
                d_date = SchemaReflector.first_existing(cols, ["development_date", "date", "created_at"]) or "development_date"
                select_fields.append(table.c[d_date].label("development_date") if d_date in table.c else literal_column("NULL").label("development_date"))
            elif category == "proposal":
                agency_col = SchemaReflector.first_existing(cols, AGENCY_COLUMNS) or "agency"
                dur_col = SchemaReflector.first_existing(cols, ["duration", "project_duration"]) or "duration"
                select_fields.append(table.c[agency_col].label("agency") if agency_col in table.c else literal("").label("agency"))
                select_fields.append(table.c[dur_col].label("duration") if dur_col in table.c else literal("").label("duration"))


            stmt = select(*select_fields)
            if email_col and email_col in table.c and f_email and f_email in faculty_table.c:
                t_email_col = table.c[email_col]
                f_email_col = faculty_table.c[f_email]
                join_clause = func.lower(func.trim(t_email_col)) == func.lower(func.trim(f_email_col))
                stmt = stmt.select_from(table.join(faculty_table, join_clause))
            else:
                stmt = stmt.select_from(table)

            clauses = []
            if "is_active" in faculty_table.c:
                clauses.append(faculty_table.c.is_active == True)

            if title_col and title_col in table.c:
                t_title_col = table.c[title_col]
                clauses.append(t_title_col.isnot(None))
                clauses.append(func.trim(t_title_col) != "")

            if filters.get("academic_year") and year_col in table.c:
                clauses.append(func.cast(table.c[year_col], text("VARCHAR")) == str(filters["academic_year"]))

            if filters.get("school") and f_school in faculty_table.c:
                clauses.append(faculty_table.c[f_school] == filters["school"])

            if filters.get("department") and f_dept in faculty_table.c:
                clauses.append(faculty_table.c[f_dept] == filters["department"])

            if filters.get("designation") and f_desig in faculty_table.c:
                clauses.append(faculty_table.c[f_desig] == filters["designation"])

            if clauses:
                stmt = stmt.where(and_(*clauses))

            result = self.db.execute(stmt).fetchall()
            rows = []
            for r in result:
                rd = dict(r._mapping)
                em = str(rd.get("f_email") or rd.get("t_email") or "").lower().strip()
                rd["faculty_email"] = em
                rd["amount"] = float(rd.get("amount") or 0.0)
                rd["score"] = float(rd.get("score") or 0.0)

                if category == "patent":
                    rd["patent_status"] = rd.get("status")
                elif category == "ipr":
                    rd["ipr_status"] = rd.get("status")
                elif category in ("internal_project", "external_project"):
                    rd["project_status"] = rd.get("status")
                    rd["sanctioned_amount"] = rd["amount"]
                    rd["external_project"] = (category == "external_project")
                elif category == "product":
                    rd["product_title"] = rd.get("title")

                rows.append(rd)
            return rows

        except Exception:
            return []


    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        tables = self._get_tables()
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        active_email_map = {p["email"]: p for p in active_faculty_profiles if p["email"]}

        proposals = self._get_records_from_table(tables["proposals"], "proposal", filters)
        int_projects = self._get_records_from_table(tables["internal_projects"], "internal_project", filters)
        ext_projects = self._get_records_from_table(tables["external_projects"], "external_project", filters)
        patents = self._get_records_from_table(tables["patents"], "patent", filters)
        ipr_records = self._get_records_from_table(tables["ipr"], "ipr", filters)
        products = self._get_records_from_table(tables["products"], "product", filters)

        page_size = filters.get("page_size")
        l_proposals = proposals[:page_size] if page_size and page_size > 0 else proposals
        l_int_projects = int_projects[:page_size] if page_size and page_size > 0 else int_projects
        l_ext_projects = ext_projects[:page_size] if page_size and page_size > 0 else ext_projects
        l_patents = patents[:page_size] if page_size and page_size > 0 else patents
        l_ipr_records = ipr_records[:page_size] if page_size and page_size > 0 else ipr_records
        l_products = products[:page_size] if page_size and page_size > 0 else products

        all_projects = int_projects + ext_projects
        all_patents_ipr = patents + ipr_records

        proposals_submitted = len(proposals)
        projects_sanctioned = len(all_projects)
        patent_or_ipr_records = len(all_patents_ipr)
        patents_granted = sum(1 for r in patents if "grant" in str(r.get("patent_status") or r.get("status") or "").lower())
        products_developed = len(products)

        active_innovation_emails = set()
        for rec_list in [proposals, int_projects, ext_projects, patents, ipr_records, products]:
            for r in rec_list:
                if r.get("faculty_email"):
                    active_innovation_emails.add(r["faculty_email"])

        innovation_active_faculty = len(active_innovation_emails)

        # Aggregate Funnel Stages & Percentage Change
        s1 = proposals_submitted
        s2 = projects_sanctioned
        s3 = patent_or_ipr_records
        s4 = patents_granted
        s5 = products_developed

        c1_2 = round(((s2 - s1) / s1 * 100.0), 2) if s1 > 0 else 0.0
        c2_3 = round(((s3 - s2) / s2 * 100.0), 2) if s2 > 0 else 0.0
        c3_4 = round(((s4 - s3) / s3 * 100.0), 2) if s3 > 0 else 0.0
        c4_5 = round(((s5 - s4) / s4 * 100.0), 2) if s4 > 0 else 0.0

        aggregate_funnel = [
            {"stage": "Research Proposals", "count": s1, "percentage_change_from_previous_stage": 0.0},
            {"stage": "Sanctioned Projects", "count": s2, "percentage_change_from_previous_stage": c1_2},
            {"stage": "Patent or IPR", "count": s3, "percentage_change_from_previous_stage": c2_3},
            {"stage": "Granted Patents", "count": s4, "percentage_change_from_previous_stage": c3_4},
            {"stage": "Products Developed", "count": s5, "percentage_change_from_previous_stage": c4_5},
        ]

        # Breakdown maps
        dept_counts: Dict[str, Dict[str, Any]] = {}
        school_counts: Dict[str, Dict[str, Any]] = {}
        yr_counts: Dict[str, Dict[str, Any]] = {}

        def touch_dept(d: str, s: str):
            dept_counts.setdefault(d, {"school": s, "department": d, "proposals": 0, "projects": 0, "patents_ipr": 0, "granted_patents": 0, "products": 0, "funding": 0.0})
            school_counts.setdefault(s, {"school": s, "proposals": 0, "projects": 0, "patents_ipr": 0, "products": 0})

        for p in active_faculty_profiles:
            touch_dept(p.get("department") or "Unassigned", p.get("school") or "Unassigned")

        for r in proposals:
            d = r.get("department") or "Unassigned"
            s = r.get("school") or "Unassigned"
            touch_dept(d, s)
            dept_counts[d]["proposals"] += 1
            school_counts[s]["proposals"] += 1
            yr = str(r.get("academic_year") or "Unspecified")
            yr_counts.setdefault(yr, {"academic_year": yr, "proposals": 0, "projects": 0, "patents_ipr": 0, "products": 0})
            yr_counts[yr]["proposals"] += 1

        for r in all_projects:
            d = r.get("department") or "Unassigned"
            s = r.get("school") or "Unassigned"
            touch_dept(d, s)
            dept_counts[d]["projects"] += 1
            dept_counts[d]["funding"] += r["amount"]
            school_counts[s]["projects"] += 1
            yr = str(r.get("academic_year") or "Unspecified")
            yr_counts.setdefault(yr, {"academic_year": yr, "proposals": 0, "projects": 0, "patents_ipr": 0, "products": 0})
            yr_counts[yr]["projects"] += 1

        for r in all_patents_ipr:
            d = r.get("department") or "Unassigned"
            s = r.get("school") or "Unassigned"
            touch_dept(d, s)
            dept_counts[d]["patents_ipr"] += 1
            school_counts[s]["patents_ipr"] += 1
            if "grant" in str(r.get("patent_status") or r.get("status") or "").lower():
                dept_counts[d]["granted_patents"] += 1
            yr = str(r.get("academic_year") or "Unspecified")
            yr_counts.setdefault(yr, {"academic_year": yr, "proposals": 0, "projects": 0, "patents_ipr": 0, "products": 0})
            yr_counts[yr]["patents_ipr"] += 1

        for r in products:
            d = r.get("department") or "Unassigned"
            s = r.get("school") or "Unassigned"
            touch_dept(d, s)
            dept_counts[d]["products"] += 1
            school_counts[s]["products"] += 1
            yr = str(r.get("academic_year") or "Unspecified")
            yr_counts.setdefault(yr, {"academic_year": yr, "proposals": 0, "projects": 0, "patents_ipr": 0, "products": 0})
            yr_counts[yr]["products"] += 1

        dept_contribution = []
        pipeline_stages_by_department = []
        for d, data in sorted(dept_counts.items()):
            tot = data["proposals"] + data["projects"] + data["patents_ipr"] + data["products"]
            dept_contribution.append({
                "school": data["school"],
                "department": d,
                "proposals": data["proposals"],
                "projects": data["projects"],
                "patents_ipr": data["patents_ipr"],
                "products": data["products"],
                "total_innovation_outputs": tot,
            })
            pipeline_stages_by_department.append({
                "department": d,
                "proposals": data["proposals"],
                "projects": data["projects"],
                "patents_ipr": data["patents_ipr"],
                "granted_patents": data["granted_patents"],
                "products": data["products"],
            })

        school_contribution = []
        innovation_activity_by_school = []
        for s, data in sorted(school_counts.items()):
            tot = data["proposals"] + data["projects"] + data["patents_ipr"] + data["products"]
            school_contribution.append({
                "school": s,
                "proposals": data["proposals"],
                "projects": data["projects"],
                "patents_ipr": data["patents_ipr"],
                "products": data["products"],
                "total_innovation_outputs": tot,
            })
            innovation_activity_by_school.append({
                "school": s,
                "proposals": data["proposals"],
                "projects": data["projects"],
                "patents_ipr": data["patents_ipr"],
                "products": data["products"],
            })

        academic_year_comparison = [
            {
                "academic_year": yr,
                "proposals": data["proposals"],
                "projects": data["projects"],
                "patents_ipr": data["patents_ipr"],
                "products": data["products"],
            }
            for yr, data in sorted(yr_counts.items())
        ]

        # Faculty Innovation Diversity
        fac_categories: Dict[str, Set[str]] = {}
        fac_names: Dict[str, Tuple[str, str]] = {}

        def record_fac(em: str, fname: str, dept: str, cat: str):
            if em:
                fac_categories.setdefault(em, set()).add(cat)
                fac_names[em] = (fname or "Unknown", dept or "Unassigned")

        for p in active_faculty_profiles:
            record_fac(p["email"], p.get("faculty_name") or "", p.get("department") or "", "Profile")

        for r in proposals:
            record_fac(r.get("faculty_email") or "", r.get("full_name") or "", r.get("department") or "", "Proposals")
        for r in int_projects:
            record_fac(r.get("faculty_email") or "", r.get("full_name") or "", r.get("department") or "", "Internal Projects")
        for r in ext_projects:
            record_fac(r.get("faculty_email") or "", r.get("full_name") or "", r.get("department") or "", "External Projects")
        for r in patents:
            record_fac(r.get("faculty_email") or "", r.get("full_name") or "", r.get("department") or "", "Patents")
        for r in ipr_records:
            record_fac(r.get("faculty_email") or "", r.get("full_name") or "", r.get("department") or "", "IPR")
        for r in products:
            record_fac(r.get("faculty_email") or "", r.get("full_name") or "", r.get("department") or "", "Products")

        faculty_innovation_diversity = []
        fac_active_3_plus = []
        for em, cats in sorted(fac_categories.items()):
            actual_cats = cats - {"Profile"}
            if not actual_cats:
                continue
            fname, dname = fac_names.get(em, ("Unknown", "Unassigned"))
            c_list = sorted(list(actual_cats))
            c_cnt = len(c_list)
            faculty_innovation_diversity.append({
                "faculty_email": em,
                "full_name": fname,
                "department": dname,
                "categories_count": c_cnt,
                "categories": c_list,
            })
            if c_cnt >= 3:
                fac_active_3_plus.append(f"{fname} ({em})")

        # Gap Analytics
        prop_without_proj = sum(data["proposals"] for d, data in dept_counts.items() if data["proposals"] > 0 and data["projects"] == 0)
        depts_proj_no_patents = sorted([d for d, data in dept_counts.items() if data["projects"] > 0 and data["patents_ipr"] == 0])

        fac_patents_set = {r["faculty_email"] for r in all_patents_ipr if r.get("faculty_email")}
        fac_products_set = {r["faculty_email"] for r in products if r.get("faculty_email")}
        fac_patents_no_products = sorted([
            fac_names.get(em, (em, ""))[0] for em in (fac_patents_set - fac_products_set)
        ])

        depts_no_products = sorted([d for d, data in dept_counts.items() if data["products"] == 0])

        all_schools = {p.get("school") for p in active_faculty_profiles if p.get("school")}
        ext_schools = {r.get("school") for r in ext_projects if r.get("school")}
        schools_no_ext = sorted(list(all_schools - ext_schools))

        dept_fundings = [data["funding"] for data in dept_counts.values()]
        dept_prods = [data["products"] for data in dept_counts.values()]
        avg_dept_funding = (sum(dept_fundings) / len(dept_fundings)) if dept_fundings else 0.0
        avg_dept_prod = (sum(dept_prods) / len(dept_prods)) if dept_prods else 0.0

        depts_high_fund_weak_prod = sorted([
            d for d, data in dept_counts.items()
            if data["funding"] >= avg_dept_funding and data["funding"] > 0 and data["products"] <= avg_dept_prod
        ])

        summary = {
            "proposals_submitted": proposals_submitted,
            "projects_sanctioned": projects_sanctioned,
            "patent_or_ipr_records": patent_or_ipr_records,
            "patents_granted": patents_granted,
            "products_developed": products_developed,
            "innovation_active_faculty": innovation_active_faculty,
            "limitation_note": "Pipeline stages represent aggregate institutional counts. Existing database records do not contain a shared innovation identifier, so individual proposals cannot be followed reliably through every stage.",
            "aggregate_funnel": aggregate_funnel,
            "pipeline_stages_by_department": pipeline_stages_by_department,
            "innovation_activity_by_school": innovation_activity_by_school,
            "academic_year_pipeline_trend": academic_year_comparison,
            "faculty_innovation_diversity": faculty_innovation_diversity,
        }

        gap_analytics = {
            "proposals_without_corresponding_aggregate_project_activity": prop_without_proj,
            "departments_with_projects_but_no_patents": depts_proj_no_patents,
            "faculty_with_patents_but_no_products": fac_patents_no_products,
            "departments_with_no_products_developed": depts_no_products,
            "schools_with_no_external_projects": schools_no_ext,
            "faculty_active_in_three_or_more_innovation_categories": fac_active_3_plus,
            "departments_showing_strong_project_funding_but_weak_product_output": depts_high_fund_weak_prod,
        }

        return {
            "research_proposals": l_proposals,
            "research_projects": l_int_projects,
            "external_research_projects": l_ext_projects,
            "patents": l_patents,
            "ipr_records": l_ipr_records,
            "products_developed": l_products,
            "summary": summary,
            "department_contribution": dept_contribution,
            "school_contribution": school_contribution,
            "academic_year_comparison": academic_year_comparison,
            "faculty_innovation_diversity": faculty_innovation_diversity,
            "gap_analytics": gap_analytics,
        }
