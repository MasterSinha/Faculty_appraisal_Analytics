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


class FacultyPerformanceAnalyticsRepository:
    """Repository for Faculty Research Performance Analytics using SQLAlchemy Core."""

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
            if f_emp in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_emp]).like(search_term))
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

    def _get_records_for_table(self, table: Optional[Table], cat_key: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        tables = self._get_tables()
        faculty_table = tables["faculty"]
        if table is None or faculty_table is None:
            return []

        cols = SchemaReflector.column_names(table)
        f_cols = SchemaReflector.column_names(faculty_table)

        id_col = SchemaReflector.first_existing(cols, ["id", f"{cat_key}_id"]) or "id"
        email_col = SchemaReflector.first_existing(cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        title_col = SchemaReflector.first_existing(cols, TITLE_COLUMNS) or "title"
        status_col = SchemaReflector.first_existing(cols, ["patent_status", "ipr_status", "project_status", "status"]) or "status"
        year_col = SchemaReflector.first_existing(cols, YEAR_COLUMNS) or "academic_year"
        amount_col = SchemaReflector.first_existing(cols, AMOUNT_COLUMNS) or "amount"
        score_col = SchemaReflector.first_existing(cols, ["score", "self_score"]) or "score"
        hod_col = SchemaReflector.first_existing(cols, ["hod_score"]) or "hod_score"
        dir_col = SchemaReflector.first_existing(cols, ["director_score"]) or "director_score"
        dean_col = SchemaReflector.first_existing(cols, ["dean_score"]) or "dean_score"
        vc_col = SchemaReflector.first_existing(cols, ["vc_score", "vc_approved_score", "final_score"]) or "vc_score"

        f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
        f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
        f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
        f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"

        select_fields = [
            table.c[id_col].label("id") if id_col in table.c else table.c[cols[0]].label("id"),
            table.c[email_col].label("t_email") if email_col in table.c else literal("").label("t_email"),
            table.c[title_col].label("title") if title_col in table.c else literal("").label("title"),
            table.c[status_col].label("status") if status_col in table.c else literal("").label("status"),
            table.c[year_col].label("academic_year") if year_col in table.c else literal("").label("academic_year"),
            table.c[amount_col].label("amount") if amount_col in table.c else literal(0.0).label("amount"),
            table.c[score_col].label("score") if score_col in table.c else literal(0.0).label("score"),
            table.c[hod_col].label("hod_score") if hod_col in table.c else literal(0.0).label("hod_score"),
            table.c[dir_col].label("director_score") if dir_col in table.c else literal(0.0).label("director_score"),
            table.c[dean_col].label("dean_score") if dean_col in table.c else literal(0.0).label("dean_score"),
            table.c[vc_col].label("vc_score") if vc_col in table.c else literal(0.0).label("vc_score"),
            faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else literal("").label("f_email"),
            faculty_table.c[f_name].label("full_name") if f_name in faculty_table.c else literal("").label("full_name"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else literal("").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else literal("").label("school"),
        ]

        stmt = select(*select_fields)
        t_email_col = table.c[email_col] if email_col in table.c else table.c[cols[0]]
        f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]

        join_clause = func.lower(func.trim(t_email_col)) == func.lower(func.trim(f_email_col))
        stmt = stmt.select_from(table.join(faculty_table, join_clause))

        clauses = []
        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        # Valid title condition where title column exists
        if title_col in table.c:
            clauses.append(table.c[title_col].isnot(None))
            clauses.append(func.trim(table.c[title_col]) != "")

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
            rd["amount"] = float(rd.get("amount") or 0.0)
            sc = float(rd.get("score") or 0.0)
            hd = float(rd.get("hod_score") or 0.0)
            dr = float(rd.get("director_score") or 0.0)
            dn = float(rd.get("dean_score") or 0.0)
            vc = float(rd.get("vc_score") or 0.0)
            final_score = vc if vc > 0 else (dn if dn > 0 else (dr if dr > 0 else (hd if hd > 0 else sc)))
            rd["score"] = sc
            rd["final_validated_score"] = float(final_score)
            rows.append(rd)
        return rows

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        tables = self._get_tables()
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        active_email_map = {p["email"]: p for p in active_faculty_profiles if p["email"]}

        # Fetch records for all 11 categories
        categories = ["journals", "books", "patents", "ipr", "research_projects", "external_projects", "proposals", "guidance", "conferences", "awards", "products"]

        cat_records: Dict[str, List[Dict[str, Any]]] = {}
        for cat in categories:
            t = tables.get(cat)
            cat_records[cat] = self._get_records_for_table(t, cat, filters)

        # Faculty level grouping
        fac_data: Dict[str, Dict[str, Any]] = {}
        overall_years: Set[int] = set()

        for email, p in active_email_map.items():
            fac_data[email] = {
                "profile": p,
                "journals": [],
                "books": [],
                "patents": [],
                "ipr": [],
                "projects": [],
                "external_projects": [],
                "proposals": [],
                "guidance": [],
                "conferences": [],
                "awards": [],
                "products": [],
                "years_set": set(),
                "year_counts": {},
                "self_score": 0.0,
                "validated_score": 0.0,
                "funding": 0.0,
                "alerts": set(),
            }

        for cat, rows in cat_records.items():
            drawer_key = "projects" if cat == "research_projects" else cat
            for r in rows:
                em = r.get("faculty_email")
                if not em:
                    continue
                if em not in fac_data:
                    fac_data[em] = {
                        "profile": {
                            "email": em,
                            "full_name": r.get("full_name") or "Unknown",
                            "employee_id": "N/A",
                            "department": r.get("department") or "N/A",
                            "school": r.get("school") or "N/A",
                            "designation": "N/A",
                            "is_active": True,
                        },
                        "journals": [],
                        "books": [],
                        "patents": [],
                        "ipr": [],
                        "projects": [],
                        "external_projects": [],
                        "proposals": [],
                        "guidance": [],
                        "conferences": [],
                        "awards": [],
                        "products": [],
                        "years_set": set(),
                        "year_counts": {},
                        "self_score": 0.0,
                        "validated_score": 0.0,
                        "funding": 0.0,
                        "alerts": set(),
                    }

                fac = fac_data[em]
                if drawer_key in fac:
                    fac[drawer_key].append(r)


                fac["self_score"] += r.get("score", 0.0)
                fac["validated_score"] += r.get("final_validated_score", 0.0)

                if cat in ("research_projects", "external_projects"):
                    fac["funding"] += r.get("amount", 0.0)

                num_yr = parse_numeric_year(r.get("academic_year") or r.get("sanction_date") or r.get("patent_date") or r.get("award_date"))
                if num_yr:
                    fac["years_set"].add(num_yr)
                    fac["year_counts"][num_yr] = fac["year_counts"].get(num_yr, 0) + 1
                    overall_years.add(num_yr)

        sorted_overall_years = sorted(overall_years)
        max_year = sorted_overall_years[-1] if sorted_overall_years else None
        prev_year = sorted_overall_years[-2] if len(sorted_overall_years) >= 2 else None

        # Build faculty performance items
        raw_items = []
        for email, fac in fac_data.items():
            p = fac["profile"]
            j_cnt = len(fac["journals"])
            b_cnt = len(fac["books"])
            pat_cnt = len(fac["patents"])
            ipr_cnt = len(fac["ipr"])
            proj_cnt = len(fac["projects"]) + len(fac["external_projects"])
            prop_cnt = len(fac["proposals"])
            gui_cnt = len(fac["guidance"])
            conf_cnt = len(fac["conferences"])
            awd_cnt = len(fac["awards"])
            prod_cnt = len(fac["products"])

            counts_list = [j_cnt, b_cnt, pat_cnt, ipr_cnt, proj_cnt, prop_cnt, gui_cnt, conf_cnt, awd_cnt, prod_cnt]
            tot_output = sum(counts_list)
            diversity_score = sum(1 for c in counts_list if c > 0)

            years = sorted(fac["years_set"])
            first_year = years[0] if years else None
            consistency_years = len(years)

            curr_output = fac["year_counts"].get(max_year, 0) if max_year else 0
            prev_output = fac["year_counts"].get(prev_year, 0) if prev_year else 0

            drawer_records = {
                "journals": fac["journals"],
                "books": fac["books"],
                "patents": fac["patents"],
                "ipr": fac["ipr"],
                "projects": fac["projects"],
                "external_projects": fac["external_projects"],
                "proposals": fac["proposals"],
                "guidance": fac["guidance"],
                "conferences": fac["conferences"],
                "awards": fac["awards"],
                "products": fac["products"],
            }

            raw_items.append({
                "faculty_email": email,
                "full_name": p.get("full_name") or "Unknown",
                "employee_id": p.get("employee_id") or "N/A",
                "department": p.get("department") or "N/A",
                "school": p.get("school") or "N/A",
                "designation": p.get("designation") or "N/A",
                "journal_papers": j_cnt,
                "books": b_cnt,
                "patents": pat_cnt,
                "ipr_records": ipr_cnt,
                "projects": proj_cnt,
                "proposals": prop_cnt,
                "funding": round(fac["funding"], 2),
                "guidance": gui_cnt,
                "conferences": conf_cnt,
                "awards": awd_cnt,
                "products_developed": prod_cnt,
                "total_output": tot_output,
                "diversity_score": diversity_score,
                "self_score": round(fac["self_score"], 2),
                "validated_research_score": round(fac["validated_score"], 2),
                "current_year_output": curr_output,
                "previous_year_output": prev_output,
                "first_activity_year": first_year,
                "consistency_years": consistency_years,
                "missing_evidence_alerts": sorted(list(fac["alerts"])),
                "records": drawer_records,
                "counts_list": counts_list,
            })

        # Calculate averages for segment classification
        active_outputs = [item["total_output"] for item in raw_items if item["total_output"] > 0]
        active_scores = [item["validated_research_score"] for item in raw_items if item["total_output"] > 0]
        avg_output = (sum(active_outputs) / len(active_outputs)) if active_outputs else 0.0
        avg_score = (sum(active_scores) / len(active_scores)) if active_scores else 0.0

        segment_counts = {
            "research_leaders_count": 0,
            "active_contributors_count": 0,
            "emerging_researchers_count": 0,
            "specialists_count": 0,
            "declining_contributors_count": 0,
            "inactive_researchers_count": 0,
        }

        inactive_label = "No recorded research activity for the selected period."

        for item in raw_items:
            tot = item["total_output"]
            v_score = item["validated_research_score"]
            div = item["diversity_score"]
            cons = item["consistency_years"]
            first_yr = item["first_activity_year"]
            curr_out = item["current_year_output"]
            prev_out = item["previous_year_output"]
            counts = item["counts_list"]

            is_specialist = tot >= 2 and any(c >= 0.70 * tot for c in counts)

            if tot == 0:
                seg = "Inactive Researchers"
                segment_counts["inactive_researchers_count"] += 1
            elif max_year and first_yr == max_year and tot > 0:
                seg = "Emerging Researchers"
                segment_counts["emerging_researchers_count"] += 1
            elif prev_out > 0 and curr_out < prev_out:
                seg = "Declining Contributors"
                segment_counts["declining_contributors_count"] += 1
            elif is_specialist:
                seg = "Specialists"
                segment_counts["specialists_count"] += 1
            elif tot >= avg_output and tot > 0 and v_score >= avg_score and v_score > 0 and div >= 3 and cons >= 2:
                seg = "Research Leaders"
                segment_counts["research_leaders_count"] += 1
            else:
                seg = "Active Contributors"
                segment_counts["active_contributors_count"] += 1

            item["segment"] = seg
            item["status_label"] = inactive_label if tot == 0 else f"{tot} research outputs"

        # Cleanup internal helper fields
        for item in raw_items:
            item.pop("counts_list", None)

        # Sorting
        sort_by = filters.get("sort_by") or "validated_research_score"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        numeric_sort_fields = [
            "validated_research_score", "total_output", "self_score", "diversity_score",
            "journal_papers", "books", "patents", "ipr_records", "projects", "proposals",
            "funding", "guidance", "conferences", "awards", "products_developed"
        ]

        if sort_by in numeric_sort_fields:
            raw_items.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            raw_items.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_fac = len(raw_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = raw_items[start_idx:end_idx]

        # Summary
        active_fac_cnt = sum(1 for item in raw_items if item["total_output"] > 0)
        inactive_fac_cnt = total_fac - active_fac_cnt
        total_outputs = sum(item["total_output"] for item in raw_items)
        total_val_score = round(sum(item["validated_research_score"] for item in raw_items), 2)
        avg_diversity = round(sum(item["diversity_score"] for item in raw_items) / total_fac, 2) if total_fac > 0 else 0.0
        total_funding = round(sum(item["funding"] for item in raw_items), 2)

        summary = {
            "total_faculty": total_fac,
            "active_research_faculty": active_fac_cnt,
            "inactive_research_faculty": inactive_fac_cnt,
            "total_research_outputs": total_outputs,
            "total_validated_score": total_val_score,
            "average_diversity_score": avg_diversity,
            "total_funding_sanctioned": total_funding,
            "inactive_label": inactive_label,
        }

        # Charts
        top_by_output = [
            {"faculty_name": item["full_name"], "department": item["department"], "total_output": item["total_output"]}
            for item in sorted(raw_items, key=lambda x: x["total_output"], reverse=True)[:10]
        ]

        top_by_score = [
            {"faculty_name": item["full_name"], "department": item["department"], "validated_score": item["validated_research_score"]}
            for item in sorted(raw_items, key=lambda x: x["validated_research_score"], reverse=True)[:10]
        ]

        diversity_counts: Dict[int, int] = {}
        for item in raw_items:
            ds = item["diversity_score"]
            diversity_counts[ds] = diversity_counts.get(ds, 0) + 1

        diversity_dist = [
            {"diversity_score": ds, "faculty_count": cnt}
            for ds, cnt in sorted(diversity_counts.items())
        ]

        # Performance trend by year
        year_trend_map: Dict[str, Dict[str, Any]] = {}
        for yr in sorted_overall_years:
            yr_str = str(yr)
            year_trend_map[yr_str] = {"academic_year": yr_str, "total_output": 0, "validated_score": 0.0}

        for cat, rows in cat_records.items():
            for r in rows:
                num_yr = parse_numeric_year(r.get("academic_year") or r.get("sanction_date") or r.get("patent_date") or r.get("award_date"))
                if num_yr:
                    yr_str = str(num_yr)
                    year_trend_map.setdefault(yr_str, {"academic_year": yr_str, "total_output": 0, "validated_score": 0.0})
                    year_trend_map[yr_str]["total_output"] += 1
                    year_trend_map[yr_str]["validated_score"] += r.get("final_validated_score", 0.0)

        perf_trend = [
            {"academic_year": yr, "total_output": data["total_output"], "validated_score": round(data["validated_score"], 2)}
            for yr, data in sorted(year_trend_map.items())
        ]

        scatter = [
            {
                "faculty_email": item["faculty_email"],
                "faculty_name": item["full_name"],
                "department": item["department"],
                "total_output": item["total_output"],
                "diversity_score": item["diversity_score"],
            }
            for item in raw_items if item["total_output"] > 0
        ][:20]

        score_comp = [
            {
                "faculty_name": item["full_name"],
                "self_score": item["self_score"],
                "final_validated_score": item["validated_research_score"],
            }
            for item in sorted(raw_items, key=lambda x: x["validated_research_score"], reverse=True)[:10]
        ]

        charts = {
            "top_faculty_by_output": top_by_output,
            "top_faculty_by_validated_score": top_by_score,
            "research_diversity_distribution": diversity_dist,
            "faculty_performance_trend": perf_trend,
            "output_vs_participation_scatter": scatter,
            "self_vs_final_score_comparison": score_comp,
        }

        return {
            "items": paginated_items,
            "summary": summary,
            "segments": segment_counts,
            "charts": charts,
            "page": page,
            "page_size": page_size,
            "total": total_fac,
        }
