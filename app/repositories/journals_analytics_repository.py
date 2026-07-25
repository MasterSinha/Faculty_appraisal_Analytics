import re
from math import ceil
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import Table, and_, case, distinct, func, or_, select, text
from sqlalchemy.orm import Session

from app.core.constants import (
    DEPARTMENT_COLUMNS,
    EMAIL_COLUMNS,
    EMPLOYEE_COLUMNS,
    INDEXING_COLUMNS,
    NAME_COLUMNS,
    SCHOOL_COLUMNS,
    TITLE_COLUMNS,
    YEAR_COLUMNS,
)
from app.models.schema_reflector import SchemaReflector


def parse_numeric_year(year_val: Any) -> Optional[int]:
    """Extract 4-digit start year from year strings like '2023-24', '2023', etc."""
    if year_val is None:
        return None
    s = str(year_val).strip()
    match = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if match:
        return int(match.group(1))
    return None


class JournalsAnalyticsRepository:
    """Repository for Journal Publications Analytics using SQL & SQLAlchemy Core."""

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

    def _get_tables(self) -> Tuple[Optional[Table], Optional[Table]]:
        journal_table = self._logical_table(["journal_publications", "journals"])
        faculty_table = self._logical_table(["faculty_profiles", "faculty", "users"])
        return journal_table, faculty_table

    def _get_filtered_joined_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        journal_table, faculty_table = self._get_tables()
        if journal_table is None or faculty_table is None:
            return []

        j_cols = SchemaReflector.column_names(journal_table)
        f_cols = SchemaReflector.column_names(faculty_table)

        j_id = SchemaReflector.first_existing(j_cols, ["id", "journal_id", "pub_id"]) or "id"
        j_email = SchemaReflector.first_existing(j_cols, ["faculty_email", "email", "official_email"]) or "faculty_email"
        j_title = SchemaReflector.first_existing(j_cols, TITLE_COLUMNS) or "title"
        j_journal = SchemaReflector.first_existing(j_cols, ["journal", "journal_name"]) or "journal"
        j_issn = SchemaReflector.first_existing(j_cols, ["issn", "issn_number", "issn_no"]) or "issn"
        j_indexing = SchemaReflector.first_existing(j_cols, INDEXING_COLUMNS) or "indexing"
        j_year = SchemaReflector.first_existing(j_cols, YEAR_COLUMNS) or "publication_year"
        j_score = SchemaReflector.first_existing(j_cols, ["score", "self_score"]) or "score"
        j_hod = SchemaReflector.first_existing(j_cols, ["hod_score"]) or "hod_score"
        j_dir = SchemaReflector.first_existing(j_cols, ["director_score"]) or "director_score"
        j_dean = SchemaReflector.first_existing(j_cols, ["dean_score"]) or "dean_score"
        j_vc = SchemaReflector.first_existing(j_cols, ["vc_score", "vc_approved_score", "final_score"]) or "vc_score"

        f_email = SchemaReflector.first_existing(f_cols, EMAIL_COLUMNS) or "email"
        f_name = SchemaReflector.first_existing(f_cols, NAME_COLUMNS) or "full_name"
        f_emp = SchemaReflector.first_existing(f_cols, EMPLOYEE_COLUMNS) or "employee_id"
        f_dept = SchemaReflector.first_existing(f_cols, DEPARTMENT_COLUMNS) or "department"
        f_school = SchemaReflector.first_existing(f_cols, SCHOOL_COLUMNS) or "school"
        f_desig = SchemaReflector.first_existing(f_cols, ["designation", "role"]) or "designation"

        select_fields = [
            journal_table.c[j_id].label("id") if j_id in journal_table.c else journal_table.c[j_cols[0]].label("id"),
            journal_table.c[j_email].label("j_faculty_email") if j_email in journal_table.c else text("''").label("j_faculty_email"),
            journal_table.c[j_title].label("title") if j_title in journal_table.c else text("''").label("title"),
            journal_table.c[j_journal].label("journal") if j_journal in journal_table.c else text("''").label("journal"),
            journal_table.c[j_issn].label("issn") if j_issn in journal_table.c else text("''").label("issn"),
            journal_table.c[j_indexing].label("indexing") if j_indexing in journal_table.c else text("''").label("indexing"),
            journal_table.c[j_year].label("academic_year") if j_year in journal_table.c else text("''").label("academic_year"),
            journal_table.c[j_score].label("score") if j_score in journal_table.c else text("0.0").label("score"),
            journal_table.c[j_hod].label("hod_score") if j_hod in journal_table.c else text("0.0").label("hod_score"),
            journal_table.c[j_dir].label("director_score") if j_dir in journal_table.c else text("0.0").label("director_score"),
            journal_table.c[j_dean].label("dean_score") if j_dean in journal_table.c else text("0.0").label("dean_score"),
            journal_table.c[j_vc].label("vc_score") if j_vc in journal_table.c else text("0.0").label("vc_score"),
            faculty_table.c[f_email].label("f_email") if f_email in faculty_table.c else text("''").label("f_email"),
            faculty_table.c[f_name].label("faculty_name") if f_name in faculty_table.c else text("''").label("faculty_name"),
            faculty_table.c[f_emp].label("employee_id") if f_emp in faculty_table.c else text("''").label("employee_id"),
            faculty_table.c[f_dept].label("department") if f_dept in faculty_table.c else text("''").label("department"),
            faculty_table.c[f_school].label("school") if f_school in faculty_table.c else text("''").label("school"),
            faculty_table.c[f_desig].label("designation") if f_desig in faculty_table.c else text("''").label("designation"),
        ]

        stmt = select(*select_fields)

        # Join condition
        j_email_col = journal_table.c[j_email] if j_email in journal_table.c else journal_table.c[j_cols[0]]
        f_email_col = faculty_table.c[f_email] if f_email in faculty_table.c else faculty_table.c[f_cols[0]]
        join_clause = func.lower(func.trim(j_email_col)) == func.lower(func.trim(f_email_col))
        stmt = stmt.select_from(journal_table.join(faculty_table, join_clause))

        # Where conditions
        clauses = []

        # Default faculty filter: is_active = TRUE
        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        # VALID PUBLICATION CONDITION: title IS NOT NULL AND TRIM(title) <> ''
        j_title_col = journal_table.c[j_title] if j_title in journal_table.c else journal_table.c[j_cols[0]]
        clauses.append(j_title_col.isnot(None))
        clauses.append(func.trim(j_title_col) != "")

        # Dynamic filters
        if filters.get("academic_year") and j_year in journal_table.c:
            clauses.append(func.cast(journal_table.c[j_year], text("VARCHAR")) == str(filters["academic_year"]))

        if filters.get("school") and f_school in faculty_table.c:
            clauses.append(faculty_table.c[f_school] == filters["school"])

        if filters.get("department") and f_dept in faculty_table.c:
            clauses.append(faculty_table.c[f_dept] == filters["department"])

        if filters.get("designation") and f_desig in faculty_table.c:
            clauses.append(faculty_table.c[f_desig] == filters["designation"])

        if filters.get("faculty_email"):
            target_email = str(filters["faculty_email"]).lower().strip()
            clauses.append(func.lower(func.trim(f_email_col)) == target_email)

        if filters.get("indexing") and j_indexing in journal_table.c:
            target_ind = str(filters["indexing"]).lower().strip()
            clauses.append(func.lower(func.trim(journal_table.c[j_indexing])) == target_ind)

        if filters.get("journal") and j_journal in journal_table.c:
            target_j = f"%{str(filters['journal']).lower().strip()}%"
            clauses.append(func.lower(func.trim(journal_table.c[j_journal])).like(target_j))

        if filters.get("search"):
            search_term = f"%{str(filters['search']).lower().strip()}%"
            search_clauses = [
                func.lower(j_title_col).like(search_term),
                func.lower(f_email_col).like(search_term),
            ]
            if j_journal in journal_table.c:
                search_clauses.append(func.lower(journal_table.c[j_journal]).like(search_term))
            if f_name in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_name]).like(search_term))
            if f_emp in faculty_table.c:
                search_clauses.append(func.lower(faculty_table.c[f_emp]).like(search_term))
            clauses.append(or_(*search_clauses))

        if clauses:
            stmt = stmt.where(and_(*clauses))

        result = self.db.execute(stmt).fetchall()
        rows = []
        for r in result:
            row_dict = dict(r._mapping)
            # COALESCE for final_validated_score: COALESCE(vc_score, dean_score, director_score, hod_score, score, 0)
            vc = float(row_dict.get("vc_score") or 0.0)
            dn = float(row_dict.get("dean_score") or 0.0)
            dr = float(row_dict.get("director_score") or 0.0)
            hd = float(row_dict.get("hod_score") or 0.0)
            sc = float(row_dict.get("score") or 0.0)
            
            final_score = vc if vc > 0 else (dn if dn > 0 else (dr if dr > 0 else (hd if hd > 0 else sc)))
            row_dict["final_validated_score"] = float(final_score)
            row_dict["faculty_email"] = str(row_dict.get("f_email") or row_dict.get("j_faculty_email") or "").lower().strip()
            rows.append(row_dict)
        return rows

    def _get_active_faculty_profiles(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        _, faculty_table = self._get_tables()
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

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 1: GET /overview"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        total_active_faculty = len({p["email"] for p in active_faculty_profiles if p["email"]})

        joined_rows = self._get_filtered_joined_rows(filters)
        total_valid_pub_ids = {r["id"] for r in joined_rows if r.get("id") is not None}
        total_valid_journal_publications = len(total_valid_pub_ids)

        publishing_emails = {r["faculty_email"] for r in joined_rows if r.get("faculty_email")}
        publishing_faculty = len(publishing_emails)

        pub_rate = round((publishing_faculty / total_active_faculty * 100.0), 2) if total_active_faculty > 0 else 0.0
        papers_per_active = round(total_valid_journal_publications / total_active_faculty, 2) if total_active_faculty > 0 else 0.0
        papers_per_publishing = round(total_valid_journal_publications / publishing_faculty, 2) if publishing_faculty > 0 else 0.0

        indexed_count = 0
        missing_indexing_count = 0
        missing_issn_count = 0
        unique_journals: Set[str] = set()

        title_counts: Dict[str, int] = {}
        title_faculty_map: Dict[str, Set[str]] = {}

        unindexed_values = {"unindexed", "none", "n/a", "na", "not indexed", ""}

        for r in joined_rows:
            ind = str(r.get("indexing") or "").strip().lower()
            if ind and ind not in unindexed_values:
                indexed_count += 1
            else:
                missing_indexing_count += 1

            issn = str(r.get("issn") or "").strip().lower()
            if not issn or issn in ("none", "n/a", "na"):
                missing_issn_count += 1

            j_name = str(r.get("journal") or "").strip().lower()
            if j_name and j_name not in ("none", "n/a", "na"):
                unique_journals.add(j_name)

            title_clean = str(r.get("title") or "").strip().lower()
            if title_clean:
                title_counts[title_clean] = title_counts.get(title_clean, 0) + 1
                if r.get("faculty_email"):
                    title_faculty_map.setdefault(title_clean, set()).add(r["faculty_email"])

        indexed_pct = round((indexed_count / total_valid_journal_publications * 100.0), 2) if total_valid_journal_publications > 0 else 0.0
        unique_journal_count = len(unique_journals)

        duplicate_title_count = sum(1 for t, count in title_counts.items() if count > 1)
        same_title_multiple_faculty_count = sum(1 for t, fac_set in title_faculty_map.items() if len(fac_set) > 1)

        return {
            "total_valid_journal_publications": total_valid_journal_publications,
            "publishing_faculty": publishing_faculty,
            "total_active_faculty": total_active_faculty,
            "publication_participation_rate": pub_rate,
            "papers_per_active_faculty": papers_per_active,
            "papers_per_publishing_faculty": papers_per_publishing,
            "indexed_publications": indexed_count,
            "indexed_publication_percentage": indexed_pct,
            "missing_indexing_count": missing_indexing_count,
            "missing_issn_count": missing_issn_count,
            "unique_journal_count": unique_journal_count,
            "duplicate_title_count": duplicate_title_count,
            "same_title_multiple_faculty_count": same_title_multiple_faculty_count,
        }

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 2: GET /departments"""
        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        dept_active_fac: Dict[Tuple[str, str], Set[str]] = {}
        for p in active_faculty_profiles:
            s = p.get("school") or "Unassigned"
            d = p.get("department") or "Unassigned"
            dept_active_fac.setdefault((s, d), set()).add(p["email"])

        joined_rows = self._get_filtered_joined_rows(filters)

        dept_pub_rows: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for r in joined_rows:
            s = r.get("school") or "Unassigned"
            d = r.get("department") or "Unassigned"
            dept_pub_rows.setdefault((s, d), []).append(r)

        all_dept_keys = set(dept_active_fac.keys()).union(set(dept_pub_rows.keys()))

        dept_items = []
        dept_papers_list = []
        dept_part_rates = []

        # First pass to compute metrics
        raw_dept_metrics = []
        for key in sorted(all_dept_keys):
            school, department = key
            active_fac_set = dept_active_fac.get(key, set())
            active_fac_count = len(active_fac_set)

            rows = dept_pub_rows.get(key, [])
            total_papers = len(rows)

            pub_fac_set = {r["faculty_email"] for r in rows if r.get("faculty_email")}
            pub_fac_count = len(pub_fac_set)

            part_rate = round((pub_fac_count / active_fac_count * 100.0), 2) if active_fac_count > 0 else 0.0
            papers_per_active = round((total_papers / active_fac_count), 2) if active_fac_count > 0 else 0.0
            papers_per_pub = round((total_papers / pub_fac_count), 2) if pub_fac_count > 0 else 0.0

            # Top 3 faculty share
            fac_paper_counts: Dict[str, int] = {}
            for r in rows:
                fe = r.get("faculty_email")
                if fe:
                    fac_paper_counts[fe] = fac_paper_counts.get(fe, 0) + 1
            top_3_sum = sum(sorted(fac_paper_counts.values(), reverse=True)[:3])
            top_3_share = round((top_3_sum / total_papers * 100.0), 2) if total_papers > 0 else 0.0

            # YoY growth
            year_paper_counts: Dict[Any, int] = {}
            for r in rows:
                yr = r.get("academic_year")
                if yr:
                    year_paper_counts[yr] = year_paper_counts.get(yr, 0) + 1

            sorted_years = sorted(year_paper_counts.keys(), key=lambda y: parse_numeric_year(y) or 0)
            if len(sorted_years) >= 2:
                latest_yr = sorted_years[-1]
                prev_yr = sorted_years[-2]
                latest_cnt = year_paper_counts[latest_yr]
                prev_cnt = year_paper_counts[prev_yr]
                yoy_growth = round(((latest_cnt - prev_cnt) / prev_cnt * 100.0), 2) if prev_cnt > 0 else (100.0 if latest_cnt > 0 else 0.0)
            else:
                yoy_growth = 0.0

            dept_papers_list.append(total_papers)
            dept_part_rates.append(part_rate)

            raw_dept_metrics.append({
                "school": school,
                "department": department,
                "active_faculty": active_fac_count,
                "total_papers": total_papers,
                "publishing_faculty": pub_fac_count,
                "participation_rate": part_rate,
                "papers_per_active_faculty": papers_per_active,
                "papers_per_publishing_faculty": papers_per_pub,
                "top_three_faculty_contribution_share": top_3_share,
                "year_over_year_growth": yoy_growth,
            })

        avg_papers = (sum(dept_papers_list) / len(dept_papers_list)) if dept_papers_list else 0.0
        avg_part = (sum(dept_part_rates) / len(dept_part_rates)) if dept_part_rates else 50.0

        for item in raw_dept_metrics:
            is_high_output = item["total_papers"] >= avg_papers and item["total_papers"] > 0
            is_broad_part = item["participation_rate"] >= avg_part and item["participation_rate"] > 0

            if is_high_output and is_broad_part:
                quad = "High output, broad participation"
            elif is_high_output and not is_broad_part:
                quad = "High output, concentrated participation"
            elif not is_high_output and is_broad_part:
                quad = "Broad participation, moderate output"
            else:
                quad = "Low output, low participation"

            item["quadrant_classification"] = quad
            dept_items.append(item)

        # Sorting
        sort_by = filters.get("sort_by") or "total_papers"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        if sort_by in ["total_papers", "active_faculty", "publishing_faculty", "participation_rate", "papers_per_active_faculty", "papers_per_publishing_faculty", "top_three_faculty_contribution_share", "year_over_year_growth"]:
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
        """Endpoint 3: GET /faculty"""
        active_fac_profiles = self._get_active_faculty_profiles(filters)
        active_email_map = {p["email"]: p for p in active_fac_profiles if p["email"]}

        joined_rows = self._get_filtered_joined_rows(filters)

        faculty_pubs: Dict[str, List[Dict[str, Any]]] = {}
        for r in joined_rows:
            fe = r.get("faculty_email")
            if fe:
                faculty_pubs.setdefault(fe, []).append(r)

        all_emails = set(active_email_map.keys()).union(set(faculty_pubs.keys()))

        faculty_summary_map: Dict[str, Dict[str, Any]] = {}
        unindexed_values = {"unindexed", "none", "n/a", "na", "not indexed", ""}

        overall_years: Set[int] = set()

        for email in all_emails:
            profile = active_email_map.get(email, {})
            pubs = faculty_pubs.get(email, [])

            name = profile.get("faculty_name") or (pubs[0].get("faculty_name") if pubs else "Unknown")
            emp_id = profile.get("employee_id") or (pubs[0].get("employee_id") if pubs else "N/A")
            dept = profile.get("department") or (pubs[0].get("department") if pubs else "N/A")
            sch = profile.get("school") or (pubs[0].get("school") if pubs else "N/A")
            desig = profile.get("designation") or (pubs[0].get("designation") if pubs else "N/A")

            total_pubs = len(pubs)
            indexed_pubs = sum(
                1 for r in pubs
                if str(r.get("indexing") or "").strip().lower() and str(r.get("indexing") or "").strip().lower() not in unindexed_values
            )

            years_set = set()
            scores = []
            latest_val_score = 0.0

            for r in pubs:
                yr = r.get("academic_year")
                if yr:
                    num_yr = parse_numeric_year(yr)
                    if num_yr:
                        years_set.add(num_yr)
                        overall_years.add(num_yr)
                scores.append(float(r.get("final_validated_score") or 0.0))

            research_score = round(sum(scores), 2)
            if scores:
                latest_val_score = round(scores[-1], 2)  # Or max score

            faculty_summary_map[email] = {
                "faculty_email": email,
                "faculty_name": name,
                "employee_id": emp_id,
                "department": dept,
                "school": sch,
                "designation": desig,
                "total_publications": total_pubs,
                "indexed_publications": indexed_pubs,
                "academic_years_active": len(years_set),
                "years_set": years_set,
                "research_score": research_score,
                "latest_validated_score": latest_val_score,
                "pubs": pubs,
            }

        sorted_overall_years = sorted(overall_years)
        latest_year = sorted_overall_years[-1] if sorted_overall_years else None
        prev_year = sorted_overall_years[-2] if len(sorted_overall_years) >= 2 else None

        # Build list of summaries
        summary_list = list(faculty_summary_map.values())

        # Clean items for response (remove helper keys)
        def clean_item(item: Dict[str, Any]) -> Dict[str, Any]:
            res = dict(item)
            res.pop("years_set", None)
            res.pop("pubs", None)
            return res

        cleaned_summary_list = [clean_item(i) for i in summary_list]

        # Sorting for paginated main list
        sort_by = filters.get("sort_by") or "total_publications"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        if sort_by in ["total_publications", "indexed_publications", "academic_years_active", "research_score", "latest_validated_score"]:
            cleaned_summary_list.sort(key=lambda x: x.get(sort_by) or 0, reverse=reverse)
        else:
            cleaned_summary_list.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_fac = len(cleaned_summary_list)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = cleaned_summary_list[start_idx:end_idx]

        # Grouped lists:
        top_publishing_faculty = sorted(cleaned_summary_list, key=lambda x: x["total_publications"], reverse=True)[:10]

        faculty_with_zero_publications = [x for x in cleaned_summary_list if x["total_publications"] == 0]
        faculty_with_exactly_one_publication = [x for x in cleaned_summary_list if x["total_publications"] == 1]

        # Consecutive years
        faculty_publishing_consecutive_years = []
        for email, item in faculty_summary_map.items():
            years = sorted(item["years_set"])
            is_consec = False
            for i in range(len(years) - 1):
                if years[i + 1] - years[i] == 1:
                    is_consec = True
                    break
            if is_consec:
                faculty_publishing_consecutive_years.append(clean_item(item))

        # Newly active publishing faculty (published only in latest_year)
        newly_active_publishing_faculty = []
        if latest_year is not None:
            for email, item in faculty_summary_map.items():
                if item["total_publications"] > 0 and item["years_set"] == {latest_year}:
                    newly_active_publishing_faculty.append(clean_item(item))

        # Faculty output declined (latest_year pubs < prev_year pubs)
        faculty_output_declined = []
        if latest_year is not None and prev_year is not None:
            for email, item in faculty_summary_map.items():
                pubs = item["pubs"]
                latest_count = sum(1 for r in pubs if parse_numeric_year(r.get("academic_year")) == latest_year)
                prev_count = sum(1 for r in pubs if parse_numeric_year(r.get("academic_year")) == prev_year)
                if prev_count > 0 and latest_count < prev_count:
                    faculty_output_declined.append(clean_item(item))

        return {
            "total": total_fac,
            "page": page,
            "page_size": page_size,
            "items": paginated_items,
            "top_publishing_faculty": top_publishing_faculty,
            "faculty_with_zero_publications": faculty_with_zero_publications,
            "faculty_with_exactly_one_publication": faculty_with_exactly_one_publication,
            "faculty_publishing_consecutive_years": faculty_publishing_consecutive_years,
            "newly_active_publishing_faculty": newly_active_publishing_faculty,
            "faculty_output_declined": faculty_output_declined,
        }

    def quality_indexing(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 4: GET /quality-indexing"""
        joined_rows = self._get_filtered_joined_rows(filters)
        total_rows = len(joined_rows)

        indexing_counts: Dict[str, int] = {}
        indexing_scores: Dict[str, List[float]] = {}
        missing_indexing = 0
        missing_issn = 0
        journal_counts: Dict[str, int] = {}
        unique_journals: Set[str] = set()

        title_counts: Dict[str, int] = {}
        title_faculty_map: Dict[str, Set[str]] = {}

        unindexed_values = {"unindexed", "none", "n/a", "na", "not indexed", ""}

        for r in joined_rows:
            raw_ind = str(r.get("indexing") or "").strip()
            ind_lower = raw_ind.lower()
            if not raw_ind or ind_lower in unindexed_values:
                cat_name = "Unindexed / Missing"
                missing_indexing += 1
            else:
                cat_name = raw_ind.upper()

            indexing_counts[cat_name] = indexing_counts.get(cat_name, 0) + 1
            indexing_scores.setdefault(cat_name, []).append(float(r.get("final_validated_score") or 0.0))

            issn = str(r.get("issn") or "").strip().lower()
            if not issn or issn in ("none", "n/a", "na"):
                missing_issn += 1

            j_name = str(r.get("journal") or "").strip()
            if j_name and j_name.lower() not in ("none", "n/a", "na"):
                journal_counts[j_name] = journal_counts.get(j_name, 0) + 1
                unique_journals.add(j_name.lower())

            title_clean = str(r.get("title") or "").strip().lower()
            if title_clean:
                title_counts[title_clean] = title_counts.get(title_clean, 0) + 1
                if r.get("faculty_email"):
                    title_faculty_map.setdefault(title_clean, set()).add(r["faculty_email"])

        indexing_distribution = []
        for cat, cnt in sorted(indexing_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round((cnt / total_rows * 100.0), 2) if total_rows > 0 else 0.0
            indexing_distribution.append({
                "indexing": cat,
                "count": cnt,
                "percentage": pct,
            })

        most_common_journals = []
        for j_name, cnt in sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            most_common_journals.append({
                "journal": j_name,
                "count": cnt,
            })

        average_score_by_indexing = []
        for cat, scores in sorted(indexing_scores.items()):
            avg_s = round(sum(scores) / len(scores), 2) if scores else 0.0
            average_score_by_indexing.append({
                "indexing": cat,
                "average_score": avg_s,
            })

        duplicate_titles = sum(1 for t, cnt in title_counts.items() if cnt > 1)
        same_title_submitted_by_multiple_faculty = sum(1 for t, fac_set in title_faculty_map.items() if len(fac_set) > 1)

        return {
            "indexing_category_distribution": indexing_distribution,
            "missing_indexing": missing_indexing,
            "missing_issn": missing_issn,
            "most_common_journals": most_common_journals,
            "unique_journal_count": len(unique_journals),
            "duplicate_titles": duplicate_titles,
            "same_title_submitted_by_multiple_faculty": same_title_submitted_by_multiple_faculty,
            "average_score_by_indexing_type": average_score_by_indexing,
        }

    def records(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Endpoint 5: GET /records"""
        joined_rows = self._get_filtered_joined_rows(filters)

        # Sorting
        sort_by = filters.get("sort_by") or "title"
        sort_order = (filters.get("sort_order") or "desc").lower()
        reverse = (sort_order == "desc")

        numeric_sort_fields = ["id", "score", "hod_score", "director_score", "dean_score", "vc_score", "final_validated_score"]

        if sort_by in numeric_sort_fields:
            joined_rows.sort(key=lambda x: float(x.get(sort_by) or 0.0), reverse=reverse)
        else:
            joined_rows.sort(key=lambda x: str(x.get(sort_by) or "").lower(), reverse=reverse)

        total_recs = len(joined_rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = joined_rows[start_idx:end_idx]

        return {
            "total": total_recs,
            "page": page,
            "page_size": page_size,
            "items": paginated_items,
        }

    def faculty_detail(self, faculty_email: str) -> Dict[str, Any]:
        """Endpoint 6: GET /faculty/{faculty_email}"""
        target_email = str(faculty_email).lower().strip()
        filters = {"faculty_email": target_email}

        active_faculty_profiles = self._get_active_faculty_profiles(filters)
        if active_faculty_profiles:
            profile = active_faculty_profiles[0]
        else:
            profile = {
                "email": target_email,
                "faculty_name": "Faculty Member",
                "employee_id": "N/A",
                "department": "N/A",
                "school": "N/A",
                "designation": "N/A",
                "is_active": True,
            }

        joined_rows = self._get_filtered_joined_rows(filters)

        year_counts: Dict[str, int] = {}
        journal_counts: Dict[str, int] = {}
        indexing_counts: Dict[str, int] = {}
        scores = []
        unindexed_values = {"unindexed", "none", "n/a", "na", "not indexed", ""}

        for r in joined_rows:
            yr = str(r.get("academic_year") or "Unspecified").strip()
            year_counts[yr] = year_counts.get(yr, 0) + 1

            j_name = str(r.get("journal") or "Unspecified").strip()
            journal_counts[j_name] = journal_counts.get(j_name, 0) + 1

            ind = str(r.get("indexing") or "Unindexed").strip()
            if not ind or ind.lower() in unindexed_values:
                ind = "Unindexed"
            indexing_counts[ind] = indexing_counts.get(ind, 0) + 1

            scores.append(float(r.get("final_validated_score") or 0.0))

        total_score = round(sum(scores), 2)
        avg_score = round(total_score / len(scores), 2) if scores else 0.0
        max_score = round(max(scores), 2) if scores else 0.0
        latest_score = round(scores[-1], 2) if scores else 0.0

        pubs_by_year = [{"academic_year": y, "count": c} for y, c in sorted(year_counts.items())]
        j_dist = [{"journal": j, "count": c} for j, c in sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)]

        total_pubs = len(joined_rows)
        idx_dist = [
            {
                "indexing": ind,
                "count": c,
                "percentage": round((c / total_pubs * 100.0), 2) if total_pubs > 0 else 0.0,
            }
            for ind, c in sorted(indexing_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "faculty_profile": profile,
            "publication_records": joined_rows,
            "publications_by_academic_year": pubs_by_year,
            "journal_distribution": j_dist,
            "indexing_distribution": idx_dist,
            "score_summary": {
                "total_score": total_score,
                "average_score": avg_score,
                "max_score": max_score,
                "latest_validated_score": latest_score,
            },
        }

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Endpoint 7: GET /export"""
        joined_rows = self._get_filtered_joined_rows(filters)
        export_rows = []
        for r in joined_rows:
            export_rows.append({
                "ID": r.get("id"),
                "Faculty Email": r.get("faculty_email"),
                "Faculty Name": r.get("faculty_name"),
                "Employee ID": r.get("employee_id"),
                "Department": r.get("department"),
                "School": r.get("school"),
                "Designation": r.get("designation"),
                "Title": r.get("title"),
                "Journal": r.get("journal"),
                "ISSN": r.get("issn"),
                "Indexing": r.get("indexing"),
                "Academic Year": r.get("academic_year"),
                "Self Score": r.get("score"),
                "HOD Score": r.get("hod_score"),
                "Director Score": r.get("director_score"),
                "Dean Score": r.get("dean_score"),
                "VC Score": r.get("vc_score"),
                "Final Validated Score": r.get("final_validated_score"),
            })
        return export_rows
