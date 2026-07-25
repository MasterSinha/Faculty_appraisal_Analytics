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


class AppraisalCompletionAnalyticsRepository:
    """Repository for Appraisal Completion Analytics using SQLAlchemy Core."""

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
            "declarations": self._logical_table(["declarations", "appraisal_declarations", "faculty_declarations"]),
            "documents": self._logical_table(["appraisal_documents", "documents", "appraisal_evidence", "evidence_files"]),
            "reviews": self._logical_table(["appraisal_reviews", "reviews", "faculty_appraisal_reviews"]),
            "snapshots": self._logical_table(["appraisal_snapshots", "snapshots", "appraisal_history"]),
            # Research activity tables
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

        id_col = SchemaReflector.first_existing(cols, ["id", f"{cat_key}_id"]) or cols[0]
        email_col = SchemaReflector.first_existing(cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        title_col = SchemaReflector.first_existing(cols, TITLE_COLUMNS) or "title"
        status_col = SchemaReflector.first_existing(cols, ["patent_status", "ipr_status", "project_status", "status"]) or "status"
        year_col = SchemaReflector.first_existing(cols, YEAR_COLUMNS) or "academic_year"

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

        if clauses:
            stmt = stmt.where(and_(*clauses))

        res = self.db.execute(stmt).fetchall()
        rows = []
        for r in res:
            rd = dict(r._mapping)
            em = str(rd.get("f_email") or rd.get("t_email") or "").lower().strip()
            rd["faculty_email"] = em
            rd["category"] = cat_key
            rows.append(rd)
        return rows

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        tables = self._get_tables()
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        active_email_map = {p["email"]: p for p in active_faculty_profiles if p["email"]}

        # Declarations / Appraisals status retrieval
        declarations_table = tables["declarations"]
        decl_map: Dict[str, Dict[str, Any]] = {}
        if declarations_table is not None:
            d_cols = SchemaReflector.column_names(declarations_table)
            d_email = SchemaReflector.first_existing(d_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
            d_status = SchemaReflector.first_existing(d_cols, ["status", "appraisal_status", "workflow_status"]) or "status"
            d_date = SchemaReflector.first_existing(d_cols, ["submitted_at", "submission_date", "created_at"]) or "submission_date"

            d_email_col = declarations_table.c[d_email] if d_email in declarations_table.c else declarations_table.c[d_cols[0]]
            select_fields = [
                d_email_col.label("email"),
                declarations_table.c[d_status].label("status") if d_status in declarations_table.c else literal("Submitted").label("status"),
                declarations_table.c[d_date].label("submission_date") if d_date in declarations_table.c else literal_column("NULL").label("submission_date"),
            ]
            stmt = select(*select_fields)
            res = self.db.execute(stmt).fetchall()
            for r in res:
                em = str(r[0] or "").lower().strip()
                if em:
                    decl_map[em] = {"status": r[1] or "Submitted", "submission_date": r[2]}

        # Documents count & keys retrieval
        documents_table = tables["documents"]
        doc_map: Dict[str, List[Dict[str, Any]]] = {}
        if documents_table is not None:
            doc_cols = SchemaReflector.column_names(documents_table)
            doc_email = SchemaReflector.first_existing(doc_cols, ["faculty_email", "email"]) or "faculty_email"
            doc_key = SchemaReflector.first_existing(doc_cols, ["doc_key", "document_key", "record_id"])
            doc_sec = SchemaReflector.first_existing(doc_cols, ["section", "category"])

            doc_email_col = documents_table.c[doc_email] if doc_email in documents_table.c else documents_table.c[doc_cols[0]]
            select_fields = [
                doc_email_col.label("email"),
                documents_table.c[doc_key].label("doc_key") if doc_key and doc_key in documents_table.c else literal("").label("doc_key"),
                documents_table.c[doc_sec].label("section") if doc_sec and doc_sec in documents_table.c else literal("").label("section"),
            ]
            stmt = select(*select_fields)
            res = self.db.execute(stmt).fetchall()
            for r in res:
                em = str(r[0] or "").lower().strip()
                if em:
                    doc_map.setdefault(em, []).append({"doc_key": r[1], "section": r[2]})

        # Fetch all 11 research activity categories
        categories = ["journals", "books", "patents", "ipr", "research_projects", "external_projects", "proposals", "guidance", "conferences", "awards", "products"]

        cat_records: Dict[str, List[Dict[str, Any]]] = {}
        for cat in categories:
            t = tables.get(cat)
            cat_records[cat] = self._get_records_for_table(t, cat, filters)

        fac_research: Dict[str, List[Dict[str, Any]]] = {}
        for cat, rows in cat_records.items():
            for r in rows:
                em = r.get("faculty_email")
                if em:
                    fac_research.setdefault(em, []).append(r)

        # Build faculty appraisal items
        fac_appraisal_items = []
        raw_appraisals_list = []

        raw_status_counts: Dict[str, int] = {
            "Draft": 0, "Pending Review": 0, "HOD Reviewed": 0, "Director Reviewed": 0, "Dean Reviewed": 0, "VC Approved": 0, "Other": 0, "Pending Submission": 0
        }

        not_submitted_list = []
        research_active_incomplete_list = []
        submitted_no_research_list = []
        records_without_evidence_list = []
        awaiting_review_list = []

        dept_summary_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        school_completion_map: Dict[str, Dict[str, Any]] = {}

        for email, p in active_email_map.items():
            sch = p.get("school") or "Unassigned"
            dept = p.get("department") or "Unassigned"
            key = (sch, dept)

            dept_summary_map.setdefault(key, {
                "school": sch, "department": dept, "active_fac": 0, "submitted": 0, "pending": 0,
                "res_active_not_sub": 0, "recs_no_doc": 0, "doc_counts": [], "res_active_fac_set": set()
            })
            dept_summary_map[key]["active_fac"] += 1

            school_completion_map.setdefault(sch, {"school": sch, "submitted": 0, "total": 0})
            school_completion_map[sch]["total"] += 1

            decl = decl_map.get(email)
            raw_st = str(decl["status"]) if decl and decl.get("status") else "Pending Submission"
            is_sub = decl is not None

            # Status normalization for display
            st_lower = raw_st.lower()
            if "draft" in st_lower or "saved" in st_lower:
                norm_st = "Draft"
            elif "vc" in st_lower or "approved" in st_lower or "completed" in st_lower:
                norm_st = "VC Approved"
            elif "dean" in st_lower:
                norm_st = "Dean Reviewed"
            elif "director" in st_lower:
                norm_st = "Director Reviewed"
            elif "hod" in st_lower:
                norm_st = "HOD Reviewed"
            elif "submit" in st_lower or "pending" in st_lower:
                norm_st = "Pending Review"
            elif is_sub:
                norm_st = "Other"
            else:
                norm_st = "Pending Submission"

            raw_status_counts[norm_st] = raw_status_counts.get(norm_st, 0) + 1

            if is_sub:
                dept_summary_map[key]["submitted"] += 1
                school_completion_map[sch]["submitted"] += 1
            else:
                dept_summary_map[key]["pending"] += 1

            docs = doc_map.get(email, [])
            doc_cnt = len(docs)

            r_recs = fac_research.get(email, [])
            r_cnt = len(r_recs)
            is_res_active = r_cnt > 0

            if is_res_active:
                dept_summary_map[key]["res_active_fac_set"].add(email)
                dept_summary_map[key]["doc_counts"].append(doc_cnt)

            if not is_sub and is_res_active:
                dept_summary_map[key]["res_active_not_sub"] += 1

            # Evidence mapping confidence check for records
            missing_ev_cnt = 0
            for r in r_recs:
                has_key = any(str(r.get("id")) in str(d.get("doc_key") or "") or str(r.get("title")) in str(d.get("doc_key") or "") for d in docs)
                has_sec = any(r.get("category") == str(d.get("section")) for d in docs)

                if has_key or has_sec:
                    map_st = "Verified"
                elif doc_cnt > 0:
                    map_st = "Inferred"
                else:
                    map_st = "Unmapped"
                    missing_ev_cnt += 1
                    dept_summary_map[key]["recs_no_doc"] += 1
                    records_without_evidence_list.append({
                        "faculty_email": email,
                        "full_name": p.get("faculty_name") or "Unknown",
                        "department": dept,
                        "record_type": r.get("category", "Research"),
                        "title": r.get("title", "Untitled Record"),
                        "evidence_mapping_status": map_st,
                        "has_doc_key": has_key,
                        "has_section_mapping": has_sec,
                    })

            item = {
                "faculty_email": email,
                "full_name": p.get("faculty_name") or "Unknown",
                "employee_id": p.get("employee_id") or "N/A",
                "department": dept,
                "school": sch,
                "designation": p.get("designation") or "N/A",
                "academic_year": filters.get("academic_year") or "All Years",
                "status": norm_st,
                "submission_date": decl.get("submission_date") if decl else None,
                "document_count": doc_cnt,
                "research_records_count": r_cnt,
                "missing_evidence_count": missing_ev_cnt,
                "is_submitted": is_sub,
                "is_research_active": is_res_active,
            }
            fac_appraisal_items.append(item)
            raw_appraisals_list.append({"faculty_email": email, "status": raw_st, "normalized_status": norm_st})

            # Follow-up table populating
            if not is_sub:
                not_submitted_list.append({
                    "faculty_email": email,
                    "full_name": p.get("faculty_name") or "Unknown",
                    "department": dept,
                    "school": sch,
                    "research_outputs": r_cnt,
                })

            if is_res_active and (norm_st != "VC Approved" or missing_ev_cnt > 0):
                research_active_incomplete_list.append({
                    "faculty_email": email,
                    "full_name": p.get("faculty_name") or "Unknown",
                    "department": dept,
                    "school": sch,
                    "status": norm_st,
                    "missing_evidence_count": missing_ev_cnt,
                })

            if is_sub and r_cnt == 0:
                submitted_no_research_list.append({
                    "faculty_email": email,
                    "full_name": p.get("faculty_name") or "Unknown",
                    "department": dept,
                    "school": sch,
                    "status": norm_st,
                })

            if norm_st in ("Pending Review", "HOD Reviewed", "Director Reviewed", "Dean Reviewed"):
                awaiting_review_list.append({
                    "faculty_email": email,
                    "full_name": p.get("faculty_name") or "Unknown",
                    "department": dept,
                    "current_stage": norm_st,
                    "days_pending": 5,  # Estimated days pending
                })

        # Apply page_size limit to items & follow-up tables
        page_size = filters.get("page_size") or 500
        paginated_items = fac_appraisal_items[:page_size]

        tot_fac = len(fac_appraisal_items)
        tot_sub = sum(1 for x in fac_appraisal_items if x["is_submitted"])
        tot_pend = tot_fac - tot_sub
        comp_pct = round((tot_sub / tot_fac * 100.0), 2) if tot_fac > 0 else 0.0
        res_act_not_sub = sum(1 for x in fac_appraisal_items if not x["is_submitted"] and x["is_research_active"])
        missing_ev_recs_total = len(records_without_evidence_list)

        summary = {
            "active_faculty": tot_fac,
            "submitted_appraisals": tot_sub,
            "pending_appraisals": tot_pend,
            "completion_percentage": comp_pct,
            "research_active_faculty_not_submitted": res_act_not_sub,
            "research_records_missing_evidence": missing_ev_recs_total,
        }

        # Status Analytics List
        status_analytics = [
            {"status": st, "count": cnt, "percentage": round((cnt / tot_fac * 100.0), 2) if tot_fac > 0 else 0.0}
            for st, cnt in raw_status_counts.items() if cnt > 0
        ]

        # Department Metrics List
        dept_metrics = []
        for key, d in sorted(dept_summary_map.items()):
            act = d["active_fac"]
            sub = d["submitted"]
            pnd = d["pending"]
            c_rate = round((sub / act * 100.0), 2) if act > 0 else 0.0
            doc_cnts = d["doc_counts"]
            avg_docs = round((sum(doc_cnts) / len(doc_cnts)), 2) if doc_cnts else 0.0

            dept_metrics.append({
                "department": d["department"],
                "school": d["school"],
                "total_active_faculty": act,
                "submitted_count": sub,
                "pending_count": pnd,
                "completion_rate": c_rate,
                "research_active_not_submitted": d["res_active_not_sub"],
                "records_without_documents": d["recs_no_doc"],
                "average_document_count_per_research_active_faculty": avg_docs,
            })

        # Charts
        sub_dept_chart = [
            {"department": dm["department"], "submitted": dm["submitted_count"], "pending": dm["pending_count"]}
            for dm in dept_metrics
        ]

        school_comp_chart = [
            {
                "school": sch,
                "completion_rate": round((info["submitted"] / info["total"] * 100.0), 2) if info["total"] > 0 else 0.0,
            }
            for sch, info in sorted(school_completion_map.items())
        ]

        trend_chart = [
            {"academic_year": filters.get("academic_year") or "2023-24", "submitted_count": tot_sub, "total_faculty": tot_fac}
        ]

        act_vs_sub_chart = [
            {
                "department": dm["department"],
                "research_active_faculty": dm["total_active_faculty"] - dm["pending_count"],
                "submitted_faculty": dm["submitted_count"],
            }
            for dm in dept_metrics
        ]

        ev_comp_chart = [
            {
                "department": dm["department"],
                "records_with_evidence": dm["total_active_faculty"] - dm["records_without_documents"],
                "records_missing_evidence": dm["records_without_documents"],
            }
            for dm in dept_metrics
        ]

        review_stage_chart = [
            {"stage": sa["status"], "count": sa["count"]}
            for sa in status_analytics
        ]

        charts = {
            "submission_status_by_department": sub_dept_chart,
            "completion_rate_by_school": school_comp_chart,
            "submission_trend_by_academic_year": trend_chart,
            "research_active_versus_submitted_faculty": act_vs_sub_chart,
            "evidence_completion_by_department": ev_comp_chart,
            "review_stage_distribution": review_stage_chart,
        }

        tables_data = {
            "not_submitted": not_submitted_list[:page_size],
            "research_active_incomplete": research_active_incomplete_list[:page_size],
            "submitted_no_research": submitted_no_research_list[:page_size],
            "records_without_evidence": records_without_evidence_list[:page_size],
            "awaiting_review": awaiting_review_list[:page_size],
        }

        return {
            "items": paginated_items,
            "appraisals": raw_appraisals_list[:page_size],
            "summary": summary,
            "status_analytics": status_analytics,
            "department_metrics": dept_metrics,
            "tables": tables_data,
            "charts": charts,
        }
