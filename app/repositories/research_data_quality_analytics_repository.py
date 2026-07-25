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


class ResearchDataQualityAnalyticsRepository:
    """Repository for Research Data Quality Analytics using SQLAlchemy Core."""

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
            "documents": self._logical_table(["appraisal_documents", "documents", "appraisal_evidence", "evidence_files"]),
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

    def _get_all_faculty(self) -> List[Dict[str, Any]]:
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
            f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
            f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"

            select_fields = [
                faculty_table.c[f_email].label("email") if f_email and f_email in faculty_table.c else literal("").label("email"),
                faculty_table.c[f_name].label("full_name") if f_name and f_name in faculty_table.c else literal("").label("full_name"),
                faculty_table.c[f_dept].label("department") if f_dept and f_dept in faculty_table.c else literal("").label("department"),
                faculty_table.c[f_school].label("school") if f_school and f_school in faculty_table.c else literal("").label("school"),
            ]
            if "is_active" in faculty_table.c:
                select_fields.append(faculty_table.c.is_active.label("is_active"))
            else:
                select_fields.append(literal(1).label("is_active"))

            stmt = select(*select_fields)
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

    def _get_all_records_raw(self, table: Optional[Table], cat_name: str) -> List[Dict[str, Any]]:
        if table is None:
            return []

        try:
            cols = SchemaReflector.column_names(table)
            if not cols:
                return []

            id_col = SchemaReflector.first_existing(cols, ["id", f"{cat_name}_id"]) or (cols[0] if cols else None)
            email_col = SchemaReflector.first_existing(cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
            title_col = SchemaReflector.first_existing(cols, TITLE_COLUMNS) or "title"
            status_col = SchemaReflector.first_existing(cols, ["patent_status", "ipr_status", "project_status", "status"]) or "status"
            year_col = SchemaReflector.first_existing(cols, YEAR_COLUMNS) or "academic_year"
            amount_col = SchemaReflector.first_existing(cols, AMOUNT_COLUMNS) or "amount"
            score_col = SchemaReflector.first_existing(cols, ["score", "self_score"]) or "score"
            vc_col = SchemaReflector.first_existing(cols, ["vc_score", "vc_approved_score", "final_score"]) or "vc_score"

            issn_col = SchemaReflector.first_existing(cols, ["issn", "e_issn"]) or "issn"
            idx_col = SchemaReflector.first_existing(cols, ["indexing", "indexed_in"]) or "indexing"
            isbn_col = SchemaReflector.first_existing(cols, ["isbn"]) or "isbn"
            file_col = SchemaReflector.first_existing(cols, ["file_no", "application_no", "file_number"]) or "file_no"
            date_col = SchemaReflector.first_existing(cols, ["date", "patent_date", "sanction_date", "award_date"]) or "date"

            select_fields = [
                table.c[id_col].label("id") if id_col and id_col in table.c else literal(1).label("id"),
                table.c[email_col].label("faculty_email") if email_col and email_col in table.c else literal("").label("faculty_email"),
                table.c[title_col].label("title") if title_col and title_col in table.c else literal("").label("title"),
                table.c[status_col].label("status") if status_col and status_col in table.c else literal("").label("status"),
                table.c[year_col].label("academic_year") if year_col and year_col in table.c else literal("").label("academic_year"),
                table.c[amount_col].label("amount") if amount_col and amount_col in table.c else literal(0.0).label("amount"),
                table.c[score_col].label("score") if score_col and score_col in table.c else literal(0.0).label("score"),
                table.c[vc_col].label("vc_score") if vc_col and vc_col in table.c else literal(0.0).label("vc_score"),
                table.c[issn_col].label("issn") if issn_col and issn_col in table.c else literal("").label("issn"),
                table.c[idx_col].label("indexing") if idx_col and idx_col in table.c else literal("").label("indexing"),
                table.c[isbn_col].label("isbn") if isbn_col and isbn_col in table.c else literal("").label("isbn"),
                table.c[file_col].label("file_no") if file_col and file_col in table.c else literal("").label("file_no"),
                table.c[date_col].label("date") if date_col and date_col in table.c else literal("").label("date"),
            ]

            stmt = select(*select_fields)
            res = self.db.execute(stmt).fetchall()
            rows = []
            for r in res:
                rd = dict(r._mapping)
                rd["faculty_email"] = str(rd.get("faculty_email") or "").lower().strip()
                rd["table_name"] = table.name
                rd["category"] = cat_name
                rows.append(rd)
            return rows
        except Exception:
            return []


    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        tables = self._get_tables()
        all_fac_profiles = self._get_all_faculty()
        fac_email_map = {p["email"]: p for p in all_fac_profiles if p["email"]}

        categories = ["journals", "books", "patents", "ipr", "research_projects", "external_projects", "proposals", "guidance", "conferences", "awards", "products"]

        cat_records: Dict[str, List[Dict[str, Any]]] = {}
        all_raw_records: List[Dict[str, Any]] = []

        for cat in categories:
            t = tables.get(cat)
            rows = self._get_all_records_raw(t, cat)
            cat_records[cat] = rows
            all_raw_records.extend(rows)

        total_records_analyzed = len(all_raw_records) + len(all_fac_profiles)

        generated_alerts: List[Dict[str, Any]] = []
        flagged_record_ids: Set[str] = set()
        alert_id_counter = 1

        def add_alert(
            severity: str,
            alert_type: str,
            category: str,
            email: str,
            rec_title: str,
            yr: str,
            desc: str,
            action: str,
            tbl_name: str,
            rec_id: Any,
        ):
            nonlocal alert_id_counter
            prof = fac_email_map.get(email, {})
            fname = prof.get("full_name") or "Unknown Faculty"
            dept = prof.get("department") or "Unassigned"
            sch = prof.get("school") or "Unassigned"

            alert_obj = {
                "id": str(alert_id_counter),
                "severity": severity,
                "alert_type": alert_type,
                "category": category,
                "faculty_email": email,
                "faculty_name": fname,
                "department": dept,
                "school": sch,
                "record_title": rec_title or "Untitled Record",
                "academic_year": str(yr or "Unspecified"),
                "issue_description": desc,
                "suggested_action": action,
                "record_table": tbl_name,
                "record_id": rec_id,
                "open_record_url": f"/analytics/records/{tbl_name}/{rec_id}" if rec_id else None,
            }
            generated_alerts.append(alert_obj)
            flagged_record_ids.add(f"{tbl_name}_{rec_id}")
            alert_id_counter += 1

        # Check 7 & 8: Blank department or school in faculty profile
        for p in all_fac_profiles:
            if not p.get("department"):
                add_alert("Informational", "Data quality alert", "Faculty", p["email"], "Faculty Profile", "N/A", "Faculty profile is missing department assignment.", "Assign department in faculty management.", "faculty_profiles", p["email"])
            if not p.get("school"):
                add_alert("Informational", "Data quality alert", "Faculty", p["email"], "Faculty Profile", "N/A", "Faculty profile is missing school assignment.", "Assign school in faculty management.", "faculty_profiles", p["email"])

        # Title / ISSN / ISBN / Status / Amount checks across records
        title_year_fac_map: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
        title_fac_map: Dict[str, Set[str]] = {}
        isbn_map: Dict[str, List[Dict[str, Any]]] = {}
        patent_file_map: Dict[str, List[Dict[str, Any]]] = {}
        proj_title_amount_map: Dict[str, Dict[str, Any]] = {}
        fac_rec_count_map: Dict[str, int] = {}

        for r in all_raw_records:
            em = r["faculty_email"]
            tbl = r["table_name"]
            cat = r["category"]
            rid = r["id"]
            title = str(r.get("title") or "").strip()
            yr = str(r.get("academic_year") or "Unspecified")

            if em:
                fac_rec_count_map[em] = fac_rec_count_map.get(em, 0) + 1

            # Check 9: Unmatched faculty email
            if em and em not in fac_email_map:
                add_alert("Critical", "Unmatched reference", cat.capitalize(), em, title, yr, f"Faculty email '{em}' is not found in active faculty profiles.", "Verify faculty email address.", tbl, rid)

            # Check 10: Inactive faculty with new activity
            if em and em in fac_email_map and not fac_email_map[em]["is_active"]:
                add_alert("Critical", "Verification required", cat.capitalize(), em, title, yr, "Record is linked to an inactive faculty member.", "Verify active status or record assignment.", tbl, rid)

            # Check 1: Missing journal publication title
            if cat == "journals" and not title:
                add_alert("Critical", "Missing information", "Journals", em, "Untitled Publication", yr, "Journal publication record is missing a title.", "Provide valid journal publication title.", tbl, rid)

            # Check 2: Missing journal ISSN
            if cat == "journals" and not r.get("issn"):
                add_alert("Warning", "Missing information", "Journals", em, title, yr, "Journal publication record is missing ISSN.", "Update ISSN number.", tbl, rid)

            # Check 3: Missing journal indexing
            if cat == "journals" and not r.get("indexing"):
                add_alert("Warning", "Verification required", "Journals", em, title, yr, "Journal publication record is missing indexing detail.", "Verify indexing status (Scopus/WoS/UGC Care).", tbl, rid)

            # Check 4: Missing book ISBN
            if cat == "books" and not r.get("isbn"):
                add_alert("Warning", "Missing information", "Books", em, title, yr, "Book publication record is missing ISBN.", "Provide valid ISBN.", tbl, rid)

            # Check 5: Missing patent status
            if cat == "patents" and not r.get("status"):
                add_alert("Warning", "Missing information", "Patents", em, title, yr, "Patent record is missing patent status.", "Update patent status (Filed/Granted/Pending).", tbl, rid)

            # Check 6: Missing project amount
            raw_amt = r.get("amount")
            try:
                amt_val = float(raw_amt) if raw_amt is not None else None
            except (ValueError, TypeError):
                amt_val = None

            if cat in ("research_projects", "external_projects") and (amt_val is None or amt_val == 0.0):
                add_alert("Warning", "Verification required", "Projects", em, title, yr, "Research project is recorded with zero or missing sanctioned amount.", "Verify sanctioned project funding amount.", tbl, rid)

            # Check 16: Negative funding
            if amt_val is not None and amt_val < 0:
                add_alert("Critical", "Outlier", "Projects", em, title, yr, f"Project funding amount is negative ({amt_val}).", "Correct funding amount.", tbl, rid)

            # Check 17 & 18: Future patent/sanction date
            num_yr = parse_numeric_year(r.get("date") or yr)
            if num_yr and num_yr > 2026:
                add_alert("Warning", "Outlier", cat.capitalize(), em, title, yr, f"Record date contains a future year ({num_yr}).", "Verify academic year / date field.", tbl, rid)

            # Check 22: Unknown academic year
            if not yr or yr.lower() in ("unspecified", "none", "unknown", "n/a"):
                add_alert("Informational", "Data quality alert", cat.capitalize(), em, title, yr, "Academic year is unspecified or unknown.", "Assign valid academic year.", tbl, rid)

            # Grouping for duplicate checks
            if title and title.lower() not in ("untitled", "n/a"):
                t_lower = title.lower()
                key_t_yr_fac = (t_lower, yr.lower(), em)
                title_year_fac_map.setdefault(key_t_yr_fac, []).append(r)

                title_fac_map.setdefault(t_lower, set()).add(em)

                if cat == "books" and r.get("isbn"):
                    isbn_map.setdefault(str(r["isbn"]).strip(), []).append(r)

                if cat == "patents" and r.get("file_no"):
                    patent_file_map.setdefault(str(r["file_no"]).strip(), []).append(r)

                if cat in ("research_projects", "external_projects"):
                    if t_lower in proj_title_amount_map:
                        prev_rec = proj_title_amount_map[t_lower]
                        try:
                            prev_amt = float(prev_rec["amount"]) if prev_rec.get("amount") is not None else None
                        except (ValueError, TypeError):
                            prev_amt = None
                        if prev_amt != amt_val:
                            add_alert("Critical", "Possible duplicate", "Projects", em, title, yr, f"Project title matches existing project with conflicting funding amount ({amt_val} vs {prev_amt}).", "Reconcile duplicate project funding.", tbl, rid)
                    else:
                        proj_title_amount_map[t_lower] = r


        # Check 11: Duplicate title for same faculty and academic year
        for (t_lower, yr, em), rec_group in title_year_fac_map.items():
            if len(rec_group) >= 2:
                for r in rec_group[1:]:
                    add_alert("Warning", "Possible duplicate", r["category"].capitalize(), em, r.get("title") or "", yr, "Duplicate record title submitted for the same faculty and academic year.", "Merge or remove duplicate submission.", r["table_name"], r["id"])

        # Check 12: Same title submitted by different faculty
        for t_lower, fac_set in title_fac_map.items():
            if len(fac_set) >= 2:
                sample_em = list(fac_set)[0]
                add_alert("Warning", "Possible duplicate", "Multiple", sample_em, t_lower.title(), "Multiple", f"Same title '{t_lower.title()}' submitted by {len(fac_set)} different faculty members.", "Verify co-authorship / duplicate submission.", "multiple", 0)

        # Check 13: Duplicate ISBN
        for isbn, rec_group in isbn_map.items():
            if len(rec_group) >= 2:
                for r in rec_group[1:]:
                    add_alert("Warning", "Possible duplicate", "Books", r["faculty_email"], r.get("title") or "", r.get("academic_year") or "", f"Duplicate ISBN '{isbn}' found across book records.", "Verify ISBN assignment.", r["table_name"], r["id"])

        # Check 14: Duplicate patent file number
        for file_no, rec_group in patent_file_map.items():
            if len(rec_group) >= 2:
                for r in rec_group[1:]:
                    add_alert("Critical", "Possible duplicate", "Patents", r["faculty_email"], r.get("title") or "", r.get("academic_year") or "", f"Duplicate patent application file number '{file_no}' registered.", "Verify patent file number.", r["table_name"], r["id"])

        # Check 23: Extremely high record count for one faculty
        for em, cnt in fac_rec_count_map.items():
            if cnt > 30:
                add_alert("Warning", "Outlier", "Volume", em, "High Volume Activity", "Multiple", f"Faculty member has an extraordinarily high volume of recorded activities ({cnt} records).", "Review activity log for bulk data entry errors.", "faculty_profiles", em)

        # Filtering generated alerts
        filtered_alerts = []
        for a in generated_alerts:
            if filters.get("severity") and a["severity"].lower() != str(filters["severity"]).lower():
                continue
            if filters.get("category") and a["category"].lower() != str(filters["category"]).lower():
                continue
            if filters.get("department") and a["department"].lower() != str(filters["department"]).lower():
                continue
            if filters.get("school") and a["school"].lower() != str(filters["school"]).lower():
                continue
            if filters.get("academic_year") and a["academic_year"] != str(filters["academic_year"]):
                continue
            if filters.get("faculty") and str(filters["faculty"]).lower() not in a["faculty_email"].lower() and str(filters["faculty"]).lower() not in a["faculty_name"].lower():
                continue
            filtered_alerts.append(a)

        # Summary Metrics
        tot_alerts = len(filtered_alerts)
        crit_cnt = sum(1 for a in filtered_alerts if a["severity"] == "Critical")
        warn_cnt = sum(1 for a in filtered_alerts if a["severity"] == "Warning")
        info_cnt = sum(1 for a in filtered_alerts if a["severity"] == "Informational")
        flagged_cnt = len(flagged_record_ids)

        comp_pct = round(((total_records_analyzed - flagged_cnt) / total_records_analyzed * 100.0), 2) if total_records_analyzed > 0 else 100.0

        summary = {
            "total_alerts": tot_alerts,
            "critical_alerts": crit_cnt,
            "warning_alerts": warn_cnt,
            "informational_alerts": info_cnt,
            "total_records_analyzed": total_records_analyzed,
            "records_with_alerts": flagged_cnt,
            "completeness_percentage": comp_pct,
        }

        # Charts
        alerts_by_sev = [
            {"severity": "Critical", "count": crit_cnt},
            {"severity": "Warning", "count": warn_cnt},
            {"severity": "Informational", "count": info_cnt},
        ]

        cat_counts: Dict[str, int] = {}
        for a in filtered_alerts:
            cat_counts[a["category"]] = cat_counts.get(a["category"], 0) + 1
        alerts_by_cat = [{"category": k, "count": v} for k, v in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)]

        dept_flag_map: Dict[str, int] = {}
        dept_tot_map: Dict[str, int] = {}
        for p in all_fac_profiles:
            d = p.get("department") or "Unassigned"
            dept_tot_map[d] = dept_tot_map.get(d, 0) + 1

        for a in filtered_alerts:
            d = a["department"]
            dept_flag_map[d] = dept_flag_map.get(d, 0) + 1

        completeness_by_dept = [
            {
                "department": d,
                "completeness_percentage": round(((tot - dept_flag_map.get(d, 0)) / tot * 100.0), 2) if tot > 0 else 100.0,
            }
            for d, tot in sorted(dept_tot_map.items())
        ]

        type_counts: Dict[str, int] = {}
        for a in filtered_alerts:
            type_counts[a["alert_type"]] = type_counts.get(a["alert_type"], 0) + 1
        top_issue_types = [{"alert_type": k, "count": v} for k, v in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)]

        year_trend_map: Dict[str, Dict[str, int]] = {}
        for a in filtered_alerts:
            yr = a["academic_year"]
            year_trend_map.setdefault(yr, {"critical": 0, "warning": 0, "informational": 0})
            if a["severity"] == "Critical":
                year_trend_map[yr]["critical"] += 1
            elif a["severity"] == "Warning":
                year_trend_map[yr]["warning"] += 1
            else:
                year_trend_map[yr]["informational"] += 1

        alert_trend_by_year = [
            {
                "academic_year": yr,
                "critical": data["critical"],
                "warning": data["warning"],
                "informational": data["informational"],
            }
            for yr, data in sorted(year_trend_map.items())
        ]

        charts = {
            "alerts_by_severity": alerts_by_sev,
            "alerts_by_category": alerts_by_cat,
            "completeness_by_department": completeness_by_dept,
            "top_issue_types": top_issue_types,
            "alert_trend_by_year": alert_trend_by_year,
        }

        return {
            "items": filtered_alerts,
            "alerts": filtered_alerts,
            "summary": summary,
            "charts": charts,
            "completeness_percentage": comp_pct,
            "review_supported": False,
        }
