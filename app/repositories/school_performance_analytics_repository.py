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


class SchoolPerformanceAnalyticsRepository:
    """Repository for School Research Performance Analytics using SQLAlchemy Core."""

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
        tables = self._get_tables()
        active_faculty_profiles = self._get_active_faculty_profiles(filters)

        # School faculty mapping
        school_fac_map: Dict[str, List[Dict[str, Any]]] = {}
        school_dept_set: Dict[str, Set[str]] = {}

        for p in active_faculty_profiles:
            s = p.get("school") or "Unassigned"
            d = p.get("department") or "Unassigned"
            school_fac_map.setdefault(s, []).append(p)
            school_dept_set.setdefault(s, set()).add(d)

        categories = ["journals", "books", "patents", "ipr", "research_projects", "external_projects", "proposals", "guidance", "conferences", "awards", "products"]

        cat_records: Dict[str, List[Dict[str, Any]]] = {}
        for cat in categories:
            t = tables.get(cat)
            cat_records[cat] = self._get_records_for_table(t, cat, filters)

        # School data structure
        school_data: Dict[str, Dict[str, Any]] = {}
        for sch, f_list in school_fac_map.items():
            school_data[sch] = {
                "school": sch,
                "active_faculty_list": f_list,
                "departments_set": school_dept_set.get(sch, set()),
                "fac_emails": {p["email"] for p in f_list if p["email"]},
                "fac_records": {},
                "dept_records": {},
                "records_by_cat": {c: [] for c in categories},
                "total_records": 0,
                "total_funding": 0.0,
                "year_counts": {},
                "funding_agency_map": {},
                "missing_metadata_count": 0,
            }

        overall_years: Set[int] = set()

        for cat, rows in cat_records.items():
            for r in rows:
                sch = r.get("school") or "Unassigned"
                dept = r.get("department") or "Unassigned"

                if sch not in school_data:
                    school_data[sch] = {
                        "school": sch,
                        "active_faculty_list": [],
                        "departments_set": set(),
                        "fac_emails": set(),
                        "fac_records": {},
                        "dept_records": {},
                        "records_by_cat": {c: [] for c in categories},
                        "total_records": 0,
                        "total_funding": 0.0,
                        "year_counts": {},
                        "funding_agency_map": {},
                        "missing_metadata_count": 0,
                    }

                s_dict = school_data[sch]
                s_dict["departments_set"].add(dept)
                s_dict["records_by_cat"][cat].append(r)
                s_dict["total_records"] += 1

                em = r.get("faculty_email")
                if em:
                    s_dict["fac_emails"].add(em)
                    s_dict["fac_records"].setdefault(em, []).append(r)

                s_dict["dept_records"].setdefault(dept, []).append(r)

                if cat in ("research_projects", "external_projects"):
                    amt = r.get("amount", 0.0)
                    s_dict["total_funding"] += amt
                    ag = str(r.get("agency") or "Unspecified").strip()
                    if ag:
                        s_dict["funding_agency_map"].setdefault(ag, {"amount": 0.0, "count": 0})
                        s_dict["funding_agency_map"][ag]["amount"] += amt
                        s_dict["funding_agency_map"][ag]["count"] += 1

                num_yr = parse_numeric_year(r.get("academic_year"))
                if num_yr:
                    s_dict["year_counts"][num_yr] = s_dict["year_counts"].get(num_yr, 0) + 1
                    overall_years.add(num_yr)

                if cat in ("journals", "books") and not r.get("issn"):
                    s_dict["missing_metadata_count"] += 1
                elif cat in ("research_projects", "external_projects", "proposals") and not r.get("agency"):
                    s_dict["missing_metadata_count"] += 1

        sorted_overall_years = sorted(overall_years)
        max_year = sorted_overall_years[-1] if sorted_overall_years else None
        prev_year = sorted_overall_years[-2] if len(sorted_overall_years) >= 2 else None

        tot_university_output = sum(s["total_records"] for s in school_data.values())

        raw_school_items = []
        for sch, s_dict in sorted(school_data.items()):
            act_fac_cnt = len(s_dict["active_faculty_list"]) or len(s_dict["fac_emails"])
            depts_cnt = len(s_dict["departments_set"])
            pub_fac_cnt = len([em for em, recs in s_dict["fac_records"].items() if len(recs) > 0])

            tot_out = s_dict["total_records"]
            j_cnt = len(s_dict["records_by_cat"]["journals"])
            b_cnt = len(s_dict["records_by_cat"]["books"])
            pat_cnt = len(s_dict["records_by_cat"]["patents"])
            ipr_cnt = len(s_dict["records_by_cat"]["ipr"])
            int_proj_cnt = len(s_dict["records_by_cat"]["research_projects"])
            ext_proj_cnt = len(s_dict["records_by_cat"]["external_projects"])
            prop_cnt = len(s_dict["records_by_cat"]["proposals"])
            gui_cnt = len(s_dict["records_by_cat"]["guidance"])
            conf_cnt = len(s_dict["records_by_cat"]["conferences"])
            awd_cnt = len(s_dict["records_by_cat"]["awards"])
            prod_cnt = len(s_dict["records_by_cat"]["products"])

            part_rate = round((pub_fac_cnt / act_fac_cnt * 100.0), 2) if act_fac_cnt > 0 else 0.0
            papers_per_fac = round((tot_out / act_fac_cnt), 2) if act_fac_cnt > 0 else 0.0

            cat_counts = [j_cnt, b_cnt, pat_cnt, ipr_cnt, int_proj_cnt + ext_proj_cnt, prop_cnt, gui_cnt, conf_cnt, awd_cnt, prod_cnt]
            div_score = sum(1 for c in cat_counts if c > 0)

            curr_out = s_dict["year_counts"].get(max_year, 0) if max_year else 0
            prev_out = s_dict["year_counts"].get(prev_year, 0) if prev_year else 0
            yoy_growth = round(((curr_out - prev_out) / prev_out * 100.0), 2) if prev_out > 0 else 0.0

            # Dependent Researcher Share (top 20% faculty output share)
            fac_output_counts = sorted([len(recs) for recs in s_dict["fac_records"].values()], reverse=True)
            top_20_pct_count = max(1, int(len(fac_output_counts) * 0.20)) if fac_output_counts else 0
            top_output_sum = sum(fac_output_counts[:top_20_pct_count])
            dep_share = round((top_output_sum / tot_out * 100.0), 2) if tot_out > 0 else 0.0

            # Funding Agencies list
            agency_list = [
                {"agency": ag, "amount": round(info["amount"], 2), "project_count": info["count"]}
                for ag, info in sorted(s_dict["funding_agency_map"].items(), key=lambda x: x[1]["amount"], reverse=True)
            ]

            # Department Comparison
            dept_comp_list = []
            for dname in sorted(s_dict["departments_set"]):
                d_recs = s_dict["dept_records"].get(dname, [])
                d_fac_set = {r["faculty_email"] for r in d_recs if r.get("faculty_email")}
                d_funding = sum(r.get("amount", 0.0) for r in d_recs if r.get("category") in ("research_projects", "external_projects"))
                d_act_fac = sum(1 for p in s_dict["active_faculty_list"] if (p.get("department") or "Unassigned") == dname) or len(d_fac_set)
                d_part_rate = round((len(d_fac_set) / d_act_fac * 100.0), 2) if d_act_fac > 0 else 0.0
                dept_comp_list.append({
                    "department": dname,
                    "active_faculty": d_act_fac,
                    "total_output": len(d_recs),
                    "funding": round(d_funding, 2),
                    "participation_rate": d_part_rate,
                })

            data_issues = []
            if s_dict["missing_metadata_count"] > 0:
                data_issues.append(f"{s_dict['missing_metadata_count']} records have missing metadata (ISSN/ISBN/Agency).")

            detail_drawer = {
                "department_comparison": dept_comp_list,
                "faculty_participation": {"active_faculty": act_fac_cnt, "publishing_faculty": pub_fac_cnt, "participation_rate": part_rate},
                "research_category_profile": [
                    {"category": "Journals", "count": j_cnt},
                    {"category": "Books", "count": b_cnt},
                    {"category": "Patents", "count": pat_cnt},
                    {"category": "IPR", "count": ipr_cnt},
                    {"category": "Projects", "count": int_proj_cnt + ext_proj_cnt},
                    {"category": "Conferences", "count": conf_cnt},
                    {"category": "Awards", "count": awd_cnt},
                    {"category": "Products", "count": prod_cnt},
                ],
                "funding_agency_profile": agency_list,
                "patents": {"count": pat_cnt, "ipr_count": ipr_cnt},
                "guidance": {"count": gui_cnt},
                "growth": {"yoy_growth": yoy_growth},
                "data_quality_issues": data_issues,
            }

            raw_school_items.append({
                "school": sch,
                "active_faculty": act_fac_cnt,
                "departments": depts_cnt,
                "total_output": tot_out,
                "publication_participation": part_rate,
                "papers_per_faculty": papers_per_fac,
                "journal_papers": j_cnt,
                "books": b_cnt,
                "patents": pat_cnt,
                "ipr_records": ipr_cnt,
                "research_projects": int_proj_cnt,
                "external_projects": ext_proj_cnt,
                "total_funding": round(s_dict["total_funding"], 2),
                "students_guided": gui_cnt,
                "awards": awd_cnt,
                "products": prod_cnt,
                "diversity_score": div_score,
                "year_over_year_growth": yoy_growth,
                "funding_agencies": agency_list,
                "dependent_researcher_share": dep_share,
                "data_quality_issues": data_issues,
                "department_comparison": dept_comp_list,
                "detail_drawer": detail_drawer,
            })

        # Sorting
        sort_by = filters.get("sort_by") or "total_output"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        numeric_sort_fields = [
            "total_output", "publication_participation", "papers_per_faculty",
            "total_funding", "active_faculty", "year_over_year_growth", "patents"
        ]

        if sort_by in numeric_sort_fields:
            raw_school_items.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            raw_school_items.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_schools = len(raw_school_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = raw_school_items[start_idx:end_idx]

        # Primary KPI Summary
        max_output_sch = max(raw_school_items, key=lambda x: x["total_output"])["school"] if raw_school_items else "N/A"
        max_funding_sch = max(raw_school_items, key=lambda x: x["total_funding"])["school"] if raw_school_items else "N/A"
        max_part_sch = max(raw_school_items, key=lambda x: x["publication_participation"])["school"] if raw_school_items else "N/A"
        max_patent_sch = max(raw_school_items, key=lambda x: x["patents"])["school"] if raw_school_items else "N/A"
        no_ext_schs = [x["school"] for x in raw_school_items if x["external_projects"] == 0]

        summary = {
            "total_schools": total_schools,
            "highest_research_output_school": max_output_sch,
            "highest_funded_school": max_funding_sch,
            "highest_participation_school": max_part_sch,
            "highest_patent_producing_school": max_patent_sch,
            "schools_with_no_external_project": no_ext_schs,
        }

        # Insights
        insights = []
        if raw_school_items and tot_university_output > 0:
            top_pub_sch = max(raw_school_items, key=lambda x: x["journal_papers"])
            pub_pct = round((top_pub_sch["journal_papers"] / tot_university_output * 100.0), 1)
            insights.append(f"{top_pub_sch['school']} contributes the largest share of publications ({pub_pct}% of university total).")

            top_fund_per_fac = max(raw_school_items, key=lambda x: (x["total_funding"] / x["active_faculty"]) if x["active_faculty"] > 0 else 0.0)
            fund_per_fac = round((top_fund_per_fac["total_funding"] / top_fund_per_fac["active_faculty"]), 2) if top_fund_per_fac["active_faculty"] > 0 else 0.0
            insights.append(f"{top_fund_per_fac['school']} achieves the highest funding per faculty ({fund_per_fac:.2f}/faculty).")

            top_growth_sch = max(raw_school_items, key=lambda x: x["year_over_year_growth"])
            if top_growth_sch["year_over_year_growth"] > 0:
                insights.append(f"{top_growth_sch['school']} recorded the highest YoY research growth (+{top_growth_sch['year_over_year_growth']}%).")

            for x in raw_school_items:
                if x["active_faculty"] >= 20 and x["publication_participation"] < 40.0:
                    insights.append(f"{x['school']} has a low participation rate ({x['publication_participation']}%) despite high faculty strength ({x['active_faculty']} faculty).")
                    break

            for x in raw_school_items:
                if x["total_funding"] == 0.0:
                    insights.append(f"{x['school']} currently has zero external project funding.")
                    break

            for x in raw_school_items:
                if x["dependent_researcher_share"] >= 60.0:
                    insights.append(f"{x['school']} is highly dependent on key researchers (top 20% contribute {x['dependent_researcher_share']}% of outputs).")
                    break

        # Charts
        cat_comp = [
            {
                "school": x["school"],
                "journals": x["journal_papers"],
                "books": x["books"],
                "patents": x["patents"],
                "projects": x["research_projects"] + x["external_projects"],
                "conferences": x["detail_drawer"]["research_category_profile"][5]["count"] if x.get("detail_drawer") else 0,
            }
            for x in raw_school_items
        ]

        part_by_school = [
            {"school": x["school"], "publication_participation": x["publication_participation"]}
            for x in sorted(raw_school_items, key=lambda s: s["publication_participation"], reverse=True)
        ]

        funding_by_school = [
            {"school": x["school"], "total_funding": x["total_funding"]}
            for x in sorted(raw_school_items, key=lambda s: s["total_funding"], reverse=True)
        ]

        patent_ipr = [
            {"school": x["school"], "patents": x["patents"], "ipr": x["ipr_records"]}
            for x in sorted(raw_school_items, key=lambda s: (s["patents"] + s["ipr_records"]), reverse=True)
        ]

        trend_map: Dict[str, Dict[str, Any]] = {}
        for yr in sorted_overall_years:
            yr_str = str(yr)
            trend_map[yr_str] = {"academic_year": yr_str, "total_output": 0, "total_funding": 0.0}

        for cat, rows in cat_records.items():
            for r in rows:
                num_yr = parse_numeric_year(r.get("academic_year"))
                if num_yr:
                    yr_str = str(num_yr)
                    trend_map.setdefault(yr_str, {"academic_year": yr_str, "total_output": 0, "total_funding": 0.0})
                    trend_map[yr_str]["total_output"] += 1
                    if cat in ("research_projects", "external_projects"):
                        trend_map[yr_str]["total_funding"] += r.get("amount", 0.0)

        year_trend = [
            {"academic_year": yr, "total_output": data["total_output"], "total_funding": round(data["total_funding"], 2)}
            for yr, data in sorted(trend_map.items())
        ]

        diversity = [
            {"school": x["school"], "diversity_score": x["diversity_score"]}
            for x in raw_school_items
        ]

        contrib_pct = [
            {
                "school": x["school"],
                "percentage": round((x["total_output"] / tot_university_output * 100.0), 2) if tot_university_output > 0 else 0.0,
            }
            for x in raw_school_items
        ]

        charts = {
            "research_category_comparison_by_school": cat_comp,
            "publication_participation_by_school": part_by_school,
            "funding_by_school": funding_by_school,
            "patent_ipr_contribution_by_school": patent_ipr,
            "academic_year_trend": year_trend,
            "school_research_diversity": diversity,
            "school_contribution_percentage_to_university_output": contrib_pct,
        }

        return {
            "items": paginated_items,
            "summary": summary,
            "charts": charts,
            "insights": insights,
            "page": page,
            "page_size": page_size,
            "total": total_schools,
        }
