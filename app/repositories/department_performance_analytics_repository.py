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


def is_pseudo_department(dept_name: Optional[str]) -> bool:
    if dept_name is None:
        return True
    d_str = str(dept_name).strip()
    if not d_str:
        return True
    d_lower = d_str.lower()
    if d_lower in {"unassigned", "unknown", "not specified", "n/a", "-", "null", "undefined", "none"}:
        return True
    if "no department mapped" in d_lower:
        return True
    return False


class DepartmentPerformanceAnalyticsRepository:
    """Repository for Department Research Performance Analytics using SQLAlchemy Core."""

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

        if filters.get("search"):
            search_term = f"%{str(filters['search']).lower().strip()}%"
            search_clauses = [
                func.lower(faculty_table.c[f_email]).like(search_term),
                func.lower(faculty_table.c[f_name]).like(search_term),
            ]
            if f_dept in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_dept]).like(search_term))
            if f_school in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_school]).like(search_term))
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
        agency_col = SchemaReflector.first_existing(cols, AGENCY_COLUMNS) or "agency"
        issn_col = SchemaReflector.first_existing(cols, ["issn", "e_issn", "isbn"]) or "issn"

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
            table.c[agency_col].label("agency") if agency_col in table.c else literal("").label("agency"),
            table.c[issn_col].label("issn_isbn") if issn_col in table.c else literal("").label("issn_isbn"),
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
            rd["score"] = float(rd.get("score") or 0.0)
            rd["category"] = cat_key
            rows.append(rd)
        return rows

    def get_analytics(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        # Always force school to 'SoEMR' for department performance endpoint
        filters = {**filters, "school": "SoEMR"}

        tables = self._get_tables()
        active_faculty_profiles = self._get_active_faculty_profiles(filters)

        # Department faculty mapping
        dept_fac_map: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for p in active_faculty_profiles:
            s = p.get("school") or "SoEMR"
            d = p.get("department") or ""
            if is_pseudo_department(d):
                continue
            dept_fac_map.setdefault((s, d), []).append(p)

        categories = ["journals", "books", "patents", "ipr", "research_projects", "external_projects", "proposals", "guidance", "conferences", "awards", "products"]

        cat_records: Dict[str, List[Dict[str, Any]]] = {}
        for cat in categories:
            t = tables.get(cat)
            cat_records[cat] = self._get_records_for_table(t, cat, filters)

        # Department data structure
        dept_data: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for key, f_list in dept_fac_map.items():
            sch, dept = key
            if is_pseudo_department(dept):
                continue
            dept_data[key] = {
                "school": sch,
                "department": dept,
                "active_faculty_list": f_list,
                "fac_emails": {p["email"] for p in f_list if p["email"]},
                "fac_records": {},
                "records_by_cat": {c: [] for c in categories},
                "total_records": 0,
                "funding": 0.0,
                "year_counts": {},
                "funding_agency_map": {},
                "patent_status": {"granted": 0, "filed": 0, "pending": 0, "other": 0},
                "missing_metadata_count": 0,
            }

        overall_years: Set[int] = set()

        for cat, rows in cat_records.items():
            for r in rows:
                sch = r.get("school") or "SoEMR"
                dept = r.get("department") or ""
                if is_pseudo_department(dept):
                    continue
                key = (sch, dept)
                if key not in dept_data:
                    dept_data[key] = {
                        "school": sch,
                        "department": dept,
                        "active_faculty_list": [],
                        "fac_emails": set(),
                        "fac_records": {},
                        "records_by_cat": {c: [] for c in categories},
                        "total_records": 0,
                        "funding": 0.0,
                        "year_counts": {},
                        "funding_agency_map": {},
                        "patent_status": {"granted": 0, "filed": 0, "pending": 0, "other": 0},
                        "missing_metadata_count": 0,
                    }


                d = dept_data[key]
                d["records_by_cat"][cat].append(r)
                d["total_records"] += 1

                em = r.get("faculty_email")
                if em:
                    d["fac_emails"].add(em)
                    d["fac_records"].setdefault(em, []).append(r)

                if cat in ("research_projects", "external_projects"):
                    amt = r.get("amount", 0.0)
                    d["funding"] += amt
                    ag = str(r.get("agency") or "Unspecified").strip()
                    if ag:
                        d["funding_agency_map"].setdefault(ag, {"amount": 0.0, "count": 0})
                        d["funding_agency_map"][ag]["amount"] += amt
                        d["funding_agency_map"][ag]["count"] += 1

                if cat == "patents":
                    st = str(r.get("status") or "").lower()
                    if "grant" in st:
                        d["patent_status"]["granted"] += 1
                    elif "file" in st:
                        d["patent_status"]["filed"] += 1
                    elif "pend" in st:
                        d["patent_status"]["pending"] += 1
                    else:
                        d["patent_status"]["other"] += 1

                num_yr = parse_numeric_year(r.get("academic_year"))
                if num_yr:
                    d["year_counts"][num_yr] = d["year_counts"].get(num_yr, 0) + 1
                    overall_years.add(num_yr)

                # Check metadata completeness
                if cat in ("journals", "books") and not r.get("issn_isbn"):
                    d["missing_metadata_count"] += 1
                elif cat in ("research_projects", "external_projects", "proposals") and not r.get("agency"):
                    d["missing_metadata_count"] += 1

        sorted_overall_years = sorted(overall_years)
        max_year = sorted_overall_years[-1] if sorted_overall_years else None
        prev_year = sorted_overall_years[-2] if len(sorted_overall_years) >= 2 else None

        raw_dept_items = []
        for key, d in sorted(dept_data.items()):
            act_fac_cnt = len(d["active_faculty_list"]) or len(d["fac_emails"])
            pub_fac_cnt = len([em for em, recs in d["fac_records"].items() if len(recs) > 0])

            tot_out = d["total_records"]
            j_cnt = len(d["records_by_cat"]["journals"])
            b_cnt = len(d["records_by_cat"]["books"])
            pat_cnt = len(d["records_by_cat"]["patents"])
            ipr_cnt = len(d["records_by_cat"]["ipr"])
            proj_cnt = len(d["records_by_cat"]["research_projects"]) + len(d["records_by_cat"]["external_projects"])
            prop_cnt = len(d["records_by_cat"]["proposals"])
            gui_cnt = len(d["records_by_cat"]["guidance"])
            conf_cnt = len(d["records_by_cat"]["conferences"])
            awd_cnt = len(d["records_by_cat"]["awards"])
            prod_cnt = len(d["records_by_cat"]["products"])

            part_rate = round((pub_fac_cnt / act_fac_cnt * 100.0), 2) if act_fac_cnt > 0 else 0.0
            papers_per_fac = round((tot_out / act_fac_cnt), 2) if act_fac_cnt > 0 else 0.0
            inact_fac_pct = round(((act_fac_cnt - pub_fac_cnt) / act_fac_cnt * 100.0), 2) if act_fac_cnt > 0 else 0.0

            cat_counts = [j_cnt, b_cnt, pat_cnt, ipr_cnt, proj_cnt, prop_cnt, gui_cnt, conf_cnt, awd_cnt, prod_cnt]
            div_score = sum(1 for c in cat_counts if c > 0)

            curr_out = d["year_counts"].get(max_year, 0) if max_year else 0
            prev_out = d["year_counts"].get(prev_year, 0) if prev_year else 0
            yoy_growth = round(((curr_out - prev_out) / prev_out * 100.0), 2) if prev_out > 0 else 0.0

            # Health Score Components (0 to 100)
            c_part = min(part_rate, 100.0)
            c_out = min((papers_per_fac / 4.0) * 100.0, 100.0)
            c_fund = min((d["funding"] / (act_fac_cnt * 100000.0)) * 100.0, 100.0) if act_fac_cnt > 0 else 0.0
            c_pat = min(((pat_cnt + ipr_cnt) / act_fac_cnt) * 50.0, 100.0) if act_fac_cnt > 0 else 0.0
            c_gui = min((gui_cnt / act_fac_cnt) * 50.0, 100.0) if act_fac_cnt > 0 else 0.0
            c_yoy = min(max(yoy_growth + 50.0, 0.0), 100.0)

            health_components = {
                "publication_participation": round(c_part, 2),
                "output_per_faculty": round(c_out, 2),
                "funding_performance": round(c_fund, 2),
                "patent_ipr_performance": round(c_pat, 2),
                "research_guidance": round(c_gui, 2),
                "yoy_growth": round(c_yoy, 2),
            }

            h_score = round(
                0.30 * c_part + 0.20 * c_out + 0.15 * c_fund + 0.15 * c_pat + 0.10 * c_gui + 0.10 * c_yoy, 2
            )

            if h_score >= 80.0:
                h_cat = "Excellent"
            elif h_score >= 65.0:
                h_cat = "Strong"
            elif h_score >= 45.0:
                h_cat = "Developing"
            else:
                h_cat = "Needs Attention"

            # Completeness & Concentrations
            comp_pct = round(((tot_out - d["missing_metadata_count"]) / tot_out * 100.0), 2) if tot_out > 0 else 100.0

            # Funding Concentration
            agency_amounts = [info["amount"] for info in d["funding_agency_map"].values()]
            max_agency_amt = max(agency_amounts) if agency_amounts else 0.0
            fund_conc = round((max_agency_amt / d["funding"] * 100.0), 2) if d["funding"] > 0 else 0.0

            # Research Concentration (top 20% faculty output share)
            fac_output_counts = sorted([len(recs) for recs in d["fac_records"].values()], reverse=True)
            top_20_pct_count = max(1, int(len(fac_output_counts) * 0.20)) if fac_output_counts else 0
            top_output_sum = sum(fac_output_counts[:top_20_pct_count])
            res_conc = round((top_output_sum / tot_out * 100.0), 2) if tot_out > 0 else 0.0

            # Top Faculty list
            fac_summary_list = []
            for em, recs in d["fac_records"].items():
                fname = recs[0].get("full_name") if recs else em
                v_sc = sum(r.get("score", 0.0) for r in recs)
                fac_summary_list.append({
                    "faculty_name": fname,
                    "faculty_email": em,
                    "total_output": len(recs),
                    "validated_score": round(v_sc, 2),
                })
            top_fac_list = sorted(fac_summary_list, key=lambda x: x["total_output"], reverse=True)[:5]

            # Funding Agencies list
            agency_list = [
                {"agency": ag, "amount": round(info["amount"], 2), "project_count": info["count"]}
                for ag, info in sorted(d["funding_agency_map"].items(), key=lambda x: x[1]["amount"], reverse=True)
            ]

            # Gaps & Quality Issues
            gaps = []
            if part_rate < 50.0:
                gaps.append(f"Low faculty research participation rate ({part_rate}%).")
            if pat_cnt == 0 and ipr_cnt == 0:
                gaps.append("No patent or IPR records registered.")
            if res_conc > 60.0:
                gaps.append(f"High research concentration: top 20% faculty contribute {res_conc}% of outputs.")

            data_issues = []
            if d["missing_metadata_count"] > 0:
                data_issues.append(f"{d['missing_metadata_count']} records have missing metadata (ISSN/ISBN/Agency).")

            detail_drawer = {
                "faculty_distribution": [
                    {"status": "Publishing / Active", "count": pub_fac_cnt},
                    {"status": "Inactive in period", "count": act_fac_cnt - pub_fac_cnt},
                ],
                "category_contributions": [
                    {"category": "Journals", "count": j_cnt},
                    {"category": "Books", "count": b_cnt},
                    {"category": "Patents", "count": pat_cnt},
                    {"category": "IPR", "count": ipr_cnt},
                    {"category": "Projects", "count": proj_cnt},
                    {"category": "Conferences", "count": conf_cnt},
                    {"category": "Awards", "count": awd_cnt},
                    {"category": "Products", "count": prod_cnt},
                ],
                "top_faculty": top_fac_list,
                "research_concentration": res_conc,
                "funding_agencies": agency_list,
                "patent_status": d["patent_status"],
                "guidance_participation": {"guidance_count": gui_cnt},
                "gaps": gaps,
                "data_quality_issues": data_issues,
            }

            raw_dept_items.append({
                "school": d["school"],
                "department": d["department"],
                "active_faculty": act_fac_cnt,
                "total_research_output": tot_out,
                "publishing_faculty": pub_fac_cnt,
                "publication_participation_rate": part_rate,
                "papers_per_active_faculty": papers_per_fac,
                "journal_papers": j_cnt,
                "books": b_cnt,
                "patents": pat_cnt,
                "ipr_records": ipr_cnt,
                "projects": proj_cnt,
                "funding": round(d["funding"], 2),
                "research_guidance": gui_cnt,
                "diversity_score": div_score,
                "year_over_year_growth": yoy_growth,
                "research_health_score": h_score,
                "health_category": h_cat,
                "health_components": health_components,
                "inactive_faculty_percentage": inact_fac_pct,
                "data_completeness": comp_pct,
                "funding_concentration": fund_conc,
                "research_concentration": res_conc,
                "top_faculty": top_fac_list,
                "funding_agencies": agency_list,
                "patent_status": d["patent_status"],
                "gaps": gaps,
                "data_quality_issues": data_issues,
                "detail_drawer": detail_drawer,
            })

        # Sorting
        sort_by = filters.get("sort_by") or "research_health_score"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        numeric_sort_fields = [
            "research_health_score", "total_research_output", "publication_participation_rate",
            "papers_per_active_faculty", "funding", "active_faculty", "year_over_year_growth"
        ]

        if sort_by in numeric_sort_fields:
            raw_dept_items.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            raw_dept_items.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_depts = len(raw_dept_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = raw_dept_items[start_idx:end_idx]

        # Summary
        tot_act_fac = sum(d["active_faculty"] for d in raw_dept_items)
        tot_outputs = sum(d["total_research_output"] for d in raw_dept_items)
        avg_part_rate = round(sum(d["publication_participation_rate"] for d in raw_dept_items) / total_depts, 2) if total_depts > 0 else 0.0
        avg_health = round(sum(d["research_health_score"] for d in raw_dept_items) / total_depts, 2) if total_depts > 0 else 0.0
        tot_funding = round(sum(d["funding"] for d in raw_dept_items), 2)
        exc_depts = sum(1 for d in raw_dept_items if d["health_category"] == "Excellent")
        attn_depts = sum(1 for d in raw_dept_items if d["health_category"] == "Needs Attention")

        summary = {
            "total_departments": total_depts,
            "total_active_faculty": tot_act_fac,
            "total_research_outputs": tot_outputs,
            "average_participation_rate": avg_part_rate,
            "average_health_score": avg_health,
            "total_funding_sanctioned": tot_funding,
            "excellent_health_departments": exc_depts,
            "needs_attention_departments": attn_depts,
        }

        # Charts
        output_ranking = [
            {"department": d["department"], "school": d["school"], "total_output": d["total_research_output"]}
            for d in sorted(raw_dept_items, key=lambda x: x["total_research_output"], reverse=True)[:10]
        ]

        part_ranking = [
            {"department": d["department"], "participation_rate": d["publication_participation_rate"]}
            for d in sorted(raw_dept_items, key=lambda x: x["publication_participation_rate"], reverse=True)[:10]
        ]

        funding_ranking = [
            {"department": d["department"], "funding": d["funding"]}
            for d in sorted(raw_dept_items, key=lambda x: x["funding"], reverse=True)[:10]
        ]

        patent_ipr_activity = [
            {"department": d["department"], "patents": d["patents"], "ipr": d["ipr_records"]}
            for d in sorted(raw_dept_items, key=lambda x: (x["patents"] + x["ipr_records"]), reverse=True)[:10]
        ]

        heatmap = [
            {
                "department": d["department"],
                "journals": d["journal_papers"],
                "books": d["books"],
                "patents": d["patents"],
                "projects": d["projects"],
                "conferences": d.get("detail_drawer", {}).get("category_contributions", [{}])[5].get("count", 0) if d.get("detail_drawer") else 0,
            }
            for d in raw_dept_items[:15]
        ]

        yoy_chart = [
            {"department": d["department"], "yoy_growth": d["year_over_year_growth"]}
            for d in sorted(raw_dept_items, key=lambda x: x["year_over_year_growth"], reverse=True)[:10]
        ]

        health_breakdown = [
            {
                "department": d["department"],
                "health_score": d["research_health_score"],
                "category": d["health_category"],
                "components": d["health_components"],
            }
            for d in raw_dept_items[:10]
        ]

        charts = {
            "department_output_ranking": output_ranking,
            "participation_rate_by_department": part_ranking,
            "funding_by_department": funding_ranking,
            "patent_ipr_activity": patent_ipr_activity,
            "department_category_heatmap": heatmap,
            "year_over_year_growth": yoy_chart,
            "research_health_score_breakdown": health_breakdown,
        }

        meta = {
            "scope": "SoEMR departments only",
            "school_filter_forced": "SoEMR",
            "reason": "Only SoEMR has department-level structure in this institution.",
        }

        return {
            "items": paginated_items,
            "summary": summary,
            "charts": charts,
            "page": page,
            "page_size": page_size,
            "total": total_depts,
            "meta": meta,
        }
