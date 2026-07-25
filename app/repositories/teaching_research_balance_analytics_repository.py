import re
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import Table, and_, case, distinct, func, literal, literal_column, or_, select, text
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


def parse_numeric_year(val: Any) -> Optional[int]:
    if val is None:
        return None
    s = str(val).strip()
    match = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if match:
        return int(match.group(1))
    return None


class TeachingResearchBalanceAnalyticsRepository:
    """Repository for Teaching vs Research Analytics using SQLAlchemy Core."""

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
            "faculty": self._logical_table(["faculty_profiles", "faculty", "users"]),
            # Teaching sources
            "teaching_process": self._logical_table(["teaching_process", "teaching_processes"]),
            "student_feedback": self._logical_table(["student_feedback", "feedback"]),
            "innovative_teaching": self._logical_table(["innovative_teaching", "innovative_pedagogy"]),
            "ict_pedagogy": self._logical_table(["ict_pedagogy", "ict_usage", "ict_tools"]),
            "course_files": self._logical_table(["course_files", "course_file"]),
            "self_development": self._logical_table(["self_development", "faculty_development", "fdp"]),
            # Research sources
            "journals": self._logical_table(["journal_publications", "journals"]),
            "books": self._logical_table(["book_publications", "books"]),
            "patents": self._logical_table(["patents"]),
            "ipr": self._logical_table(["ipr_records"]),
            "research_projects": self._logical_table(["research_projects", "internal_research_projects"]),
            "external_projects": self._logical_table(["external_research_projects", "external_projects"]),
            "proposals": self._logical_table(["research_proposals", "proposals"]),
            "guidance": self._logical_table(["research_guidance", "guidance"]),
            "conferences": self._logical_table(["conferences", "confrences"]),
            "awards": self._logical_table(["awards"]),
            "products": self._logical_table(["products_developed", "products"]),
        }

    def _get_active_faculty_profiles(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        tables = self._get_tables()
        faculty_table = tables["faculty"]
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
            faculty_table.c[f_name].label("full_name") if f_name in faculty_table.c else literal("").label("full_name"),
            faculty_table.c[f_emp].label("employee_id") if f_emp in faculty_table.c else literal("").label("employee_id"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else literal("").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else literal("").label("school"),
            faculty_table.c[f_desig].label("designation") if f_desig in faculty_table.c else literal("").label("designation"),
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
        if filters.get("faculty"):
            target_fac = str(filters["faculty"]).lower().strip()
            clauses.append(
                or_(
                    func.lower(func.trim(faculty_table.c[f_email])) == target_fac,
                    func.lower(faculty_table.c[f_name]).like(f"%{target_fac}%"),
                )
            )

        if filters.get("search"):
            search_term = f"%{str(filters['search']).lower().strip()}%"
            search_clauses = [
                func.lower(faculty_table.c[f_email]).like(search_term),
                func.lower(faculty_table.c[f_name]).like(search_term),
            ]
            if f_dept in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_dept]).like(search_term))
            clauses.append(or_(*search_clauses))

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

    def _get_records_for_table(self, table: Optional[Table], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        tables = self._get_tables()
        faculty_table = tables["faculty"]
        if table is None or faculty_table is None:
            return []

        cols = SchemaReflector.column_names(table)
        f_cols = SchemaReflector.column_names(faculty_table)

        id_col = SchemaReflector.first_existing(cols, ["id"]) or cols[0]
        email_col = SchemaReflector.first_existing(cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        title_col = SchemaReflector.first_existing(cols, TITLE_COLUMNS)
        year_col = SchemaReflector.first_existing(cols, YEAR_COLUMNS) or "academic_year"
        score_col = SchemaReflector.first_existing(cols, ["score", "self_score", "marks", "obtained_marks", "feedback_score"]) or "score"
        vc_col = SchemaReflector.first_existing(cols, ["vc_score", "vc_approved_score", "final_score", "approved_score"]) or "vc_score"

        f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
        f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
        f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
        f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"

        select_fields = [
            table.c[id_col].label("id") if id_col in table.c else table.c[cols[0]].label("id"),
            table.c[email_col].label("t_email") if email_col in table.c else literal("").label("t_email"),
            table.c[year_col].label("academic_year") if year_col in table.c else literal("").label("academic_year"),
            table.c[score_col].label("score") if score_col in table.c else literal(0.0).label("score"),
            table.c[vc_col].label("vc_score") if vc_col in table.c else literal(0.0).label("vc_score"),
            faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else literal("").label("f_email"),
            faculty_table.c[f_name].label("full_name") if f_name in faculty_table.c else literal("").label("full_name"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else literal("").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else literal("").label("school"),
        ]
        if title_col and title_col in table.c:
            select_fields.append(table.c[title_col].label("title"))

        stmt = select(*select_fields)
        t_email_col = table.c[email_col] if email_col in table.c else table.c[cols[0]]
        f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]

        join_clause = func.lower(func.trim(t_email_col)) == func.lower(func.trim(f_email_col))
        stmt = stmt.select_from(table.join(faculty_table, join_clause))

        clauses = []
        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        if filters.get("academic_year") and year_col in table.c:
            clauses.append(func.cast(table.c[year_col], text("VARCHAR")) == str(filters["academic_year"]))
        if filters.get("school") and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])
        if filters.get("department") and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])

        if clauses:
            stmt = stmt.where(and_(*clauses))

        res = self.db.execute(stmt).fetchall()
        rows = []
        for r in res:
            rd = dict(r._mapping)
            em = str(rd.get("f_email") or rd.get("t_email") or "").lower().strip()
            rd["faculty_email"] = em
            sc = float(rd.get("score") or 0.0)
            vc = float(rd.get("vc_score") or 0.0)
            rd["validated_score"] = vc if vc > 0 else sc
            rows.append(rd)
        return rows

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        tables = self._get_tables()
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        active_email_map = {p["email"]: p for p in active_faculty_profiles if p["email"]}

        teaching_keys = ["teaching_process", "student_feedback", "innovative_teaching", "ict_pedagogy", "course_files", "self_development"]
        research_keys = ["journals", "books", "patents", "ipr", "research_projects", "external_projects", "proposals", "guidance", "conferences", "awards", "products"]

        teaching_records: Dict[str, List[Dict[str, Any]]] = {}
        for key in teaching_keys:
            teaching_records[key] = self._get_records_for_table(tables.get(key), filters)

        research_records: Dict[str, List[Dict[str, Any]]] = {}
        for key in research_keys:
            research_records[key] = self._get_records_for_table(tables.get(key), filters)

        fac_scores: Dict[str, Dict[str, Any]] = {}
        for email, p in active_email_map.items():
            fac_scores[email] = {
                "profile": p,
                "teaching_process": 0.0,
                "student_feedback": 0.0,
                "innovative_teaching": 0.0,
                "ict_pedagogy": 0.0,
                "course_files": 0.0,
                "self_development": 0.0,
                "publications": 0.0,
                "projects": 0.0,
                "patents": 0.0,
                "academic_years": set(),
            }

        # Populate teaching scores
        for key, rows in teaching_records.items():
            for r in rows:
                em = r.get("faculty_email")
                if not em:
                    continue
                if em not in fac_scores:
                    fac_scores[em] = {
                        "profile": {
                            "email": em,
                            "full_name": r.get("full_name") or "Unknown",
                            "employee_id": "N/A",
                            "department": r.get("department") or "N/A",
                            "school": r.get("school") or "N/A",
                            "designation": "N/A",
                            "is_active": True,
                        },
                        "teaching_process": 0.0,
                        "student_feedback": 0.0,
                        "innovative_teaching": 0.0,
                        "ict_pedagogy": 0.0,
                        "course_files": 0.0,
                        "self_development": 0.0,
                        "publications": 0.0,
                        "projects": 0.0,
                        "patents": 0.0,
                        "academic_years": set(),
                    }
                sc = r.get("validated_score", 0.0)
                fac_scores[em][key] += sc
                num_yr = parse_numeric_year(r.get("academic_year"))
                if num_yr:
                    fac_scores[em]["academic_years"].add(num_yr)

        # Populate research scores
        for key, rows in research_records.items():
            for r in rows:
                em = r.get("faculty_email")
                if not em:
                    continue
                if em not in fac_scores:
                    fac_scores[em] = {
                        "profile": {
                            "email": em,
                            "full_name": r.get("full_name") or "Unknown",
                            "employee_id": "N/A",
                            "department": r.get("department") or "N/A",
                            "school": r.get("school") or "N/A",
                            "designation": "N/A",
                            "is_active": True,
                        },
                        "teaching_process": 0.0,
                        "student_feedback": 0.0,
                        "innovative_teaching": 0.0,
                        "ict_pedagogy": 0.0,
                        "course_files": 0.0,
                        "self_development": 0.0,
                        "publications": 0.0,
                        "projects": 0.0,
                        "patents": 0.0,
                        "academic_years": set(),
                    }
                sc = r.get("validated_score", 0.0)
                if key in ("journals", "books", "conferences"):
                    fac_scores[em]["publications"] += sc
                elif key in ("research_projects", "external_projects", "proposals"):
                    fac_scores[em]["projects"] += sc
                else:
                    fac_scores[em]["patents"] += sc

                num_yr = parse_numeric_year(r.get("academic_year"))
                if num_yr:
                    fac_scores[em]["academic_years"].add(num_yr)

        raw_items = []
        overall_trends: Dict[str, Dict[str, Any]] = {}

        for email, fac in fac_scores.items():
            p = fac["profile"]
            tp_sc = min(fac["teaching_process"], 25.0)
            sf_sc = min(fac["student_feedback"], 25.0)
            it_sc = min(fac["innovative_teaching"], 15.0)
            ict_sc = min(fac["ict_pedagogy"], 15.0)
            cf_sc = min(fac["course_files"], 10.0)
            sd_sc = min(fac["self_development"], 10.0)

            t_total = min(tp_sc + sf_sc + it_sc + ict_sc + cf_sc + sd_sc, 100.0)
            t_pct = round((t_total / 100.0 * 100.0), 2)

            pub_sc = min(fac["publications"], 50.0)
            proj_sc = min(fac["projects"], 30.0)
            pat_sc = min(fac["patents"], 20.0)

            r_total = min(pub_sc + proj_sc + pat_sc, 100.0)
            r_pct = round((r_total / 100.0 * 100.0), 2)

            # Quadrant Rule
            if t_pct >= 60.0 and r_pct >= 60.0:
                quadrant = "Balanced Leaders"
            elif t_pct >= 60.0 and r_pct < 60.0:
                quadrant = "Teaching Focused"
            elif t_pct < 60.0 and r_pct >= 60.0:
                quadrant = "Research Focused"
            else:
                quadrant = "Development Opportunity"

            for yr in fac["academic_years"]:
                yr_str = str(yr)
                overall_trends.setdefault(yr_str, {"academic_year": yr_str, "t_pct_sum": 0.0, "r_pct_sum": 0.0, "count": 0, "balanced": 0})
                overall_trends[yr_str]["t_pct_sum"] += t_pct
                overall_trends[yr_str]["r_pct_sum"] += r_pct
                overall_trends[yr_str]["count"] += 1
                if quadrant == "Balanced Leaders":
                    overall_trends[yr_str]["balanced"] += 1

            raw_items.append({
                "faculty_email": email,
                "full_name": p.get("full_name") or "Unknown",
                "employee_id": p.get("employee_id") or "N/A",
                "department": p.get("department") or "N/A",
                "school": p.get("school") or "N/A",
                "designation": p.get("designation") or "N/A",
                "academic_year": filters.get("academic_year") or "All Years",
                "teaching_score": round(t_total, 2),
                "teaching_max_marks": 100.0,
                "teaching_score_percentage": t_pct,
                "research_score": round(r_total, 2),
                "research_max_marks": 100.0,
                "research_score_percentage": r_pct,
                "student_feedback_score": round(sf_sc, 2),
                "student_feedback_max_marks": 25.0,
                "student_feedback_score_percentage": round((sf_sc / 25.0 * 100.0), 2),
                "innovative_teaching_score": round(it_sc, 2),
                "innovative_teaching_max_marks": 15.0,
                "innovative_teaching_score_percentage": round((it_sc / 15.0 * 100.0), 2),
                "ict_usage_score": round(ict_sc, 2),
                "ict_usage_max_marks": 15.0,
                "ict_usage_score_percentage": round((ict_sc / 15.0 * 100.0), 2),
                "teaching_process_score": round(tp_sc, 2),
                "teaching_process_max_marks": 25.0,
                "teaching_process_score_percentage": round((tp_sc / 25.0 * 100.0), 2),
                "course_files_score": round(cf_sc, 2),
                "course_files_max_marks": 10.0,
                "course_files_score_percentage": round((cf_sc / 10.0 * 100.0), 2),
                "self_development_score": round(sd_sc, 2),
                "self_development_max_marks": 10.0,
                "self_development_score_percentage": round((sd_sc / 10.0 * 100.0), 2),
                "publications_score": round(pub_sc, 2),
                "publications_max_marks": 50.0,
                "publications_score_percentage": round((pub_sc / 50.0 * 100.0), 2),
                "projects_score": round(proj_sc, 2),
                "projects_max_marks": 30.0,
                "projects_score_percentage": round((proj_sc / 30.0 * 100.0), 2),
                "patents_score": round(pat_sc, 2),
                "patents_max_marks": 20.0,
                "patents_score_percentage": round((pat_sc / 20.0 * 100.0), 2),
                "quadrant": quadrant,
            })

        # Sorting
        sort_by = filters.get("sort_by") or "teaching_score_percentage"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        numeric_sort_fields = [
            "teaching_score_percentage", "research_score_percentage", "teaching_score", "research_score",
            "student_feedback_score_percentage", "publications_score_percentage"
        ]

        if sort_by in numeric_sort_fields:
            raw_items.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            raw_items.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_fac = len(raw_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = raw_items[start_idx:end_idx]

        # Primary KPI Summary & Quadrants Summary
        b_cnt = sum(1 for x in raw_items if x["quadrant"] == "Balanced Leaders")
        tf_cnt = sum(1 for x in raw_items if x["quadrant"] == "Teaching Focused")
        rf_cnt = sum(1 for x in raw_items if x["quadrant"] == "Research Focused")
        do_cnt = sum(1 for x in raw_items if x["quadrant"] == "Development Opportunity")

        avg_t_score = round(sum(x["teaching_score"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0
        avg_r_score = round(sum(x["research_score"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0

        summary = {
            "balanced_high_performers": b_cnt,
            "teaching_focused_faculty": tf_cnt,
            "research_focused_faculty": rf_cnt,
            "development_opportunity_group": do_cnt,
            "average_teaching_score": avg_t_score,
            "average_research_score": avg_r_score,
            "disclaimer": "This dashboard shows associations within recorded appraisal data. It does not prove that one activity caused another.",
        }

        quadrants = {
            "balanced_leaders_count": b_cnt,
            "teaching_focused_count": tf_cnt,
            "research_focused_count": rf_cnt,
            "development_opportunity_count": do_cnt,
        }

        # Department Balance
        dept_map: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for x in raw_items:
            key = (x["school"], x["department"])
            dept_map.setdefault(key, []).append(x)

        dept_balance = []
        for key, items in sorted(dept_map.items()):
            sch, dname = key
            fac_cnt = len(items)
            db_b = sum(1 for x in items if x["quadrant"] == "Balanced Leaders")
            db_tf = sum(1 for x in items if x["quadrant"] == "Teaching Focused")
            db_rf = sum(1 for x in items if x["quadrant"] == "Research Focused")
            db_do = sum(1 for x in items if x["quadrant"] == "Development Opportunity")
            avg_t = round(sum(x["teaching_score_percentage"] for x in items) / fac_cnt, 2)
            avg_r = round(sum(x["research_score_percentage"] for x in items) / fac_cnt, 2)
            dept_balance.append({
                "school": sch,
                "department": dname,
                "active_faculty": fac_cnt,
                "balanced_leaders": db_b,
                "teaching_focused": db_tf,
                "research_focused": db_rf,
                "development_opportunity": db_do,
                "avg_teaching_pct": avg_t,
                "avg_research_pct": avg_r,
            })

        # Teaching & Research Components Summary
        teaching_components = {
            "teaching_process_avg_pct": round(sum(x["teaching_process_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
            "student_feedback_avg_pct": round(sum(x["student_feedback_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
            "innovative_teaching_avg_pct": round(sum(x["innovative_teaching_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
            "ict_usage_avg_pct": round(sum(x["ict_usage_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
            "course_files_avg_pct": round(sum(x["course_files_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
            "self_development_avg_pct": round(sum(x["self_development_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
        }

        research_components = {
            "publications_avg_pct": round(sum(x["publications_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
            "projects_avg_pct": round(sum(x["projects_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
            "patents_avg_pct": round(sum(x["patents_score_percentage"] for x in raw_items) / total_fac, 2) if total_fac > 0 else 0.0,
        }

        # Trends
        trends = [
            {
                "academic_year": yr,
                "avg_teaching_pct": round((data["t_pct_sum"] / data["count"]), 2) if data["count"] > 0 else 0.0,
                "avg_research_pct": round((data["r_pct_sum"] / data["count"]), 2) if data["count"] > 0 else 0.0,
                "balanced_leaders_count": data["balanced"],
            }
            for yr, data in sorted(overall_trends.items())
        ]

        return {
            "items": paginated_items,
            "summary": summary,
            "quadrants": quadrants,
            "department_balance": dept_balance,
            "teaching_components": teaching_components,
            "research_components": research_components,
            "trends": trends,
            "page": page,
            "page_size": page_size,
            "total": total_fac,
        }
