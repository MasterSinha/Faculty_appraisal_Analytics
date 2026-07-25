from math import ceil
from typing import Any, Dict, List, Optional
from sqlalchemy import Table, and_, case, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import (
    DEPARTMENT_COLUMNS,
    EMAIL_COLUMNS,
    EMPLOYEE_COLUMNS,
    NAME_COLUMNS,
    SCHOOL_COLUMNS,
    YEAR_COLUMNS,
)
from app.models.schema_reflector import SchemaReflector


class BooksAnalyticsRepository:
    """Repository for Books & Chapters Analytics using SQLAlchemy Core."""

    def __init__(self, db: Session):
        self.db = db
        self.reflector = SchemaReflector(db)

    def overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Overview metrics for Books Analytics."""
        book_table = self._logical_table("book_publications")
        faculty_table = self._logical_table("faculty_profiles")
        journal_table = self._logical_table("journal_publications")

        if faculty_table is None:
            return self._empty_overview()

        # 1. Total Active Faculty in Scope
        fp_email_col = SchemaReflector.first_existing(SchemaReflector.column_names(faculty_table), EMAIL_COLUMNS) or "email"
        fp_school_col = SchemaReflector.first_existing(SchemaReflector.column_names(faculty_table), SCHOOL_COLUMNS)
        fp_dept_col = SchemaReflector.first_existing(SchemaReflector.column_names(faculty_table), DEPARTMENT_COLUMNS)
        fp_desig_col = SchemaReflector.first_existing(SchemaReflector.column_names(faculty_table), ["designation", "role"])

        fac_stmt = select(func.count(distinct(func.lower(func.trim(faculty_table.c[fp_email_col])))))
        fac_clauses = []
        if "is_active" in faculty_table.c:
            fac_clauses.append(faculty_table.c.is_active == True)
        if filters.get("school") and fp_school_col and fp_school_col in faculty_table.c:
            fac_clauses.append(faculty_table.c[fp_school_col] == filters["school"])
        if filters.get("department") and fp_dept_col and fp_dept_col in faculty_table.c:
            fac_clauses.append(faculty_table.c[fp_dept_col] == filters["department"])
        if filters.get("designation") and fp_desig_col and fp_desig_col in faculty_table.c:
            fac_clauses.append(faculty_table.c[fp_desig_col] == filters["designation"])
        if filters.get("faculty_email"):
            fac_clauses.append(func.lower(func.trim(faculty_table.c[fp_email_col])) == str(filters["faculty_email"]).lower().strip())

        if fac_clauses:
            fac_stmt = fac_stmt.where(and_(*fac_clauses))

        total_active_fac = int(self.db.execute(fac_stmt).scalar() or 0)

        if book_table is None:
            return self._empty_overview(total_active_fac)

        # 2. Get Filtered Joined Rows
        joined_rows = self._get_filtered_joined_rows(filters)
        total_records = len(joined_rows)

        publishing_emails = set()
        isbn_count = 0
        missing_isbn_count = 0
        first_author_count = 0
        coauthored_count = 0
        faculty_book_counts: Dict[str, int] = {}
        isbn_map: Dict[str, set] = {}

        for r in joined_rows:
            email = str(r.get("faculty_email") or "").lower().strip()
            if email:
                publishing_emails.add(email)
                faculty_book_counts[email] = faculty_book_counts.get(email, 0) + 1

            isbn = str(r.get("isbn") or "").strip()
            if isbn and isbn.lower() not in ("none", "null", "n/a", "0", ""):
                isbn_count += 1
                title = str(r.get("title") or r.get("book") or "").strip().lower()
                isbn_map.setdefault(isbn, set()).add(title)
            else:
                missing_isbn_count += 1

            role = str(r.get("role") or r.get("first_author") or "").lower().strip()
            if "first" in role:
                first_author_count += 1
            elif "co" in role:
                coauthored_count += 1

        pub_fac_count = len(publishing_emails)
        multiple_books_fac = sum(1 for c in faculty_book_counts.values() if c >= 2)

        duplicate_isbn_count = sum(len(titles) for isbn, titles in isbn_map.items() if len(titles) > 1 or len(titles) == 1)
        # Duplicate ISBNs = ISBNs appearing > 1 times in raw records
        raw_isbn_counts: Dict[str, int] = {}
        for r in joined_rows:
            isbn = str(r.get("isbn") or "").strip()
            if isbn and isbn.lower() not in ("none", "null", "n/a", "0", ""):
                raw_isbn_counts[isbn] = raw_isbn_counts.get(isbn, 0) + 1
        dup_isbn_sum = sum(cnt for cnt in raw_isbn_counts.values() if cnt > 1)

        same_isbn_unrelated_titles = sum(1 for titles in isbn_map.values() if len(titles) > 1)

        # 3. Journal Cross-Verification
        journal_publishing_emails = set()
        if journal_table is not None:
            j_email_col = SchemaReflector.first_existing(SchemaReflector.column_names(journal_table), ["faculty_email", "email"]) or "faculty_email"
            j_stmt = select(distinct(func.lower(func.trim(journal_table.c[j_email_col]))))
            journal_publishing_emails = {str(row[0]).lower().strip() for row in self.db.execute(j_stmt).all() if row[0]}

        books_no_journals = sum(1 for e in publishing_emails if e not in journal_publishing_emails)
        both_books_and_journals = sum(1 for e in publishing_emails if e in journal_publishing_emails)

        part_rate = round((pub_fac_count / total_active_fac * 100), 2) if total_active_fac > 0 else 0.0
        books_per_active = round((total_records / total_active_fac), 2) if total_active_fac > 0 else 0.0
        books_per_pub = round((total_records / pub_fac_count), 2) if pub_fac_count > 0 else 0.0
        isbn_comp_rate = round((isbn_count / total_records * 100), 2) if total_records > 0 else 0.0

        return {
            "total_book_publication_records": total_records,
            "faculty_publishing_books": pub_fac_count,
            "total_active_faculty": total_active_fac,
            "book_participation_rate": part_rate,
            "books_per_active_faculty": books_per_active,
            "books_per_publishing_faculty": books_per_pub,
            "publications_with_isbn": isbn_count,
            "isbn_completion_rate": isbn_comp_rate,
            "first_author_contributions": first_author_count,
            "coauthored_contributions": coauthored_count,
            "missing_isbn_count": missing_isbn_count,
            "duplicate_isbn_count": dup_isbn_sum,
            "same_isbn_unrelated_titles_count": same_isbn_unrelated_titles,
            "faculty_with_multiple_books": multiple_books_fac,
            "faculty_publishing_books_but_no_journals": books_no_journals,
            "faculty_publishing_both_books_and_journals": both_books_and_journals,
        }

    def departments(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Department-level Books Analytics with pagination & sorting."""
        faculty_table = self._logical_table("faculty_profiles")
        if faculty_table is None:
            return {"items": [], "page": page, "page_size": page_size, "total": 0, "total_pages": 0}

        fp_cols = SchemaReflector.column_names(faculty_table)
        fp_email_col = SchemaReflector.first_existing(fp_cols, EMAIL_COLUMNS) or "email"
        fp_dept_col = SchemaReflector.first_existing(fp_cols, DEPARTMENT_COLUMNS) or "department"
        fp_school_col = SchemaReflector.first_existing(fp_cols, SCHOOL_COLUMNS) or "school"

        # 1. Total Active Faculty per Dept
        dept_fac_stmt = select(
            faculty_table.c[fp_dept_col].label("department"),
            faculty_table.c[fp_school_col].label("school"),
            func.count(distinct(func.lower(func.trim(faculty_table.c[fp_email_col])))).label("active_fac"),
        ).group_by(faculty_table.c[fp_dept_col], faculty_table.c[fp_school_col])

        if "is_active" in faculty_table.c:
            dept_fac_stmt = dept_fac_stmt.where(faculty_table.c.is_active == True)

        dept_map: Dict[str, Dict[str, Any]] = {}
        for r in self.db.execute(dept_fac_stmt).all():
            dept = str(r.department or "Unassigned").strip()
            dept_map[dept] = {
                "school": str(r.school or "Unassigned").strip(),
                "department": dept,
                "active_faculty": int(r.active_fac or 0),
                "total_book_publications": 0,
                "publishing_emails": set(),
                "publications_with_isbn": 0,
                "first_author_contributions": 0,
                "coauthored_contributions": 0,
                "total_score": 0.0,
                "final_validated_score": 0.0,
            }

        # 2. Add Joined Book Data
        rows = self._get_filtered_joined_rows(filters)
        for r in rows:
            dept = str(r.get("department") or "Unassigned").strip()
            email = str(r.get("faculty_email") or "").lower().strip()
            item = dept_map.setdefault(
                dept,
                {
                    "school": str(r.get("school") or "Unassigned").strip(),
                    "department": dept,
                    "active_faculty": 1,
                    "total_book_publications": 0,
                    "publishing_emails": set(),
                    "publications_with_isbn": 0,
                    "first_author_contributions": 0,
                    "coauthored_contributions": 0,
                    "total_score": 0.0,
                    "final_validated_score": 0.0,
                },
            )
            item["total_book_publications"] += 1
            if email:
                item["publishing_emails"].add(email)

            isbn = str(r.get("isbn") or "").strip()
            if isbn and isbn.lower() not in ("none", "null", "n/a", "0", ""):
                item["publications_with_isbn"] += 1

            role = str(r.get("role") or r.get("first_author") or "").lower().strip()
            if "first" in role:
                item["first_author_contributions"] += 1
            elif "co" in role:
                item["coauthored_contributions"] += 1

            item["total_score"] += float(r.get("score") or 0.0)
            item["final_validated_score"] += float(r.get("final_validated_score") or 0.0)

        # 3. Format and Compute Derived Ratios
        dept_list = []
        for dept, d in dept_map.items():
            tot_fac = d["active_faculty"] or 1
            tot_books = d["total_book_publications"]
            pub_fac = len(d["publishing_emails"])

            d["faculty_publishing_books"] = pub_fac
            d["book_participation_rate"] = round((pub_fac / tot_fac) * 100, 2)
            d["books_per_active_faculty"] = round(tot_books / tot_fac, 2)
            d["books_per_publishing_faculty"] = round(tot_books / pub_fac, 2) if pub_fac > 0 else 0.0
            d["isbn_completion_rate"] = round((d["publications_with_isbn"] / tot_books) * 100, 2) if tot_books > 0 else 0.0
            d["total_score"] = round(d["total_score"], 2)
            d["final_validated_score"] = round(d["final_validated_score"], 2)
            del d["publishing_emails"]
            dept_list.append(d)

        # 4. Sorting & Pagination
        sort_by = filters.get("sort_by") or "total_book_publications"
        reverse = str(filters.get("sort_order") or "desc").lower() == "desc"
        dept_list = sorted(dept_list, key=lambda x: x.get(sort_by, 0), reverse=reverse)

        total = len(dept_list)
        start = (page - 1) * page_size
        paged_items = dept_list[start : start + page_size]

        return {
            "items": paged_items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": ceil(total / page_size) if total else 0,
        }

    def publishers(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compute Publisher Analytics sorted by total_books descending."""
        rows = self._get_filtered_joined_rows(filters)

        pub_map: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            pub_name = str(r.get("publisher") or "Not Specified").strip()
            email = str(r.get("faculty_email") or "").lower().strip()
            isbn = str(r.get("isbn") or "").strip()
            score = float(r.get("final_validated_score") or 0.0)

            item = pub_map.setdefault(
                pub_name,
                {"publisher": pub_name, "total_books": 0, "emails": set(), "isbn_count": 0, "total_score": 0.0},
            )
            item["total_books"] += 1
            if email:
                item["emails"].add(email)
            if isbn and isbn.lower() not in ("none", "null", "n/a", "0", ""):
                item["isbn_count"] += 1
            item["total_score"] += score

        result = []
        for pub_name, item in pub_map.items():
            tot_b = item["total_books"]
            result.append({
                "publisher": pub_name,
                "total_books": tot_b,
                "faculty_count": len(item["emails"]),
                "isbn_count": item["isbn_count"],
                "average_score": round(item["total_score"] / tot_b, 2) if tot_b > 0 else 0.0,
            })

        return sorted(result, key=lambda x: x["total_books"], reverse=True)

    def authorship(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Authorship & Collaboration Analytics."""
        rows = self._get_filtered_joined_rows(filters)

        first_author_cnt = 0
        coauthored_cnt = 0
        unspecified_cnt = 0
        first_author_fac_map: Dict[str, Dict[str, Any]] = {}
        coauthor_fac_map: Dict[str, Dict[str, Any]] = {}
        fac_total_books: Dict[str, int] = {}

        for r in rows:
            email = str(r.get("faculty_email") or "").lower().strip()
            name = str(r.get("faculty_name") or "Faculty Member")
            role = str(r.get("role") or r.get("first_author") or "").lower().strip()

            if email:
                fac_total_books[email] = fac_total_books.get(email, 0) + 1

            if "first" in role:
                first_author_cnt += 1
                if email:
                    item = first_author_fac_map.setdefault(email, {"faculty_email": email, "faculty_name": name, "count": 0})
                    item["count"] += 1
            elif "co" in role:
                coauthored_cnt += 1
                if email:
                    item = coauthor_fac_map.setdefault(email, {"faculty_email": email, "faculty_name": name, "count": 0})
                    item["count"] += 1
            else:
                unspecified_cnt += 1

        multiple_books_fac = sum(1 for cnt in fac_total_books.values() if cnt >= 2)

        top_first = sorted(first_author_fac_map.values(), key=lambda x: x["count"], reverse=True)[:5]
        top_coauthor = sorted(coauthor_fac_map.values(), key=lambda x: x["count"], reverse=True)[:5]

        return {
            "first_author_contributions": first_author_cnt,
            "coauthored_contributions": coauthored_cnt,
            "unspecified_authorship": unspecified_cnt,
            "faculty_with_multiple_books": multiple_books_fac,
            "top_first_author_faculty": top_first,
            "top_coauthor_faculty": top_coauthor,
        }

    def quality(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Data Quality & Verification Analytics."""
        rows = self._get_filtered_joined_rows(filters)
        total_records = len(rows)

        missing_isbn = 0
        missing_publisher = 0
        missing_title = 0
        isbn_map: Dict[str, List[str]] = {}
        raw_isbn_counts: Dict[str, int] = {}

        for r in rows:
            isbn = str(r.get("isbn") or "").strip()
            title = str(r.get("title") or r.get("book") or "").strip()
            publisher = str(r.get("publisher") or "").strip()

            if not title:
                missing_title += 1
            if not publisher or publisher.lower() in ("none", "null", "n/a"):
                missing_publisher += 1

            if isbn and isbn.lower() not in ("none", "null", "n/a", "0", ""):
                raw_isbn_counts[isbn] = raw_isbn_counts.get(isbn, 0) + 1
                isbn_map.setdefault(isbn, []).append(title or "Untitled Book")
            else:
                missing_isbn += 1

        dup_isbn_sum = sum(cnt for cnt in raw_isbn_counts.values() if cnt > 1)
        same_isbn_unrelated_titles = sum(1 for titles in isbn_map.values() if len(set(titles)) > 1)

        isbn_with_count = total_records - missing_isbn
        isbn_comp_rate = round((isbn_with_count / total_records * 100), 2) if total_records > 0 else 0.0

        dup_isbn_records = [
            {"isbn": isbn, "count": len(titles), "titles": list(set(titles))}
            for isbn, titles in isbn_map.items()
            if len(titles) > 1
        ]

        most_common_publishers = self.publishers(filters)[:5]

        return {
            "missing_isbn_count": missing_isbn,
            "duplicate_isbn_count": dup_isbn_sum,
            "same_isbn_unrelated_titles_count": same_isbn_unrelated_titles,
            "missing_publisher_count": missing_publisher,
            "missing_title_and_book_count": missing_title,
            "isbn_completion_rate": isbn_comp_rate,
            "most_common_publishers": most_common_publishers,
            "duplicate_isbn_records": dup_isbn_records,
        }

    def records(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Paginated Detailed Book Records."""
        rows = self._get_filtered_joined_rows(filters)

        search = str(filters.get("search") or "").lower().strip()
        if search:
            rows = [
                r for r in rows
                if search in str(r.get("title", "")).lower()
                or search in str(r.get("book", "")).lower()
                or search in str(r.get("faculty_name", "")).lower()
                or search in str(r.get("publisher", "")).lower()
                or search in str(r.get("isbn", "")).lower()
            ]

        sort_by = filters.get("sort_by") or "title"
        reverse = str(filters.get("sort_order") or "desc").lower() == "desc"
        rows = sorted(rows, key=lambda r: str(r.get(sort_by) or ""), reverse=reverse)

        total = len(rows)
        start = (page - 1) * page_size
        paged_rows = rows[start : start + page_size]

        items = []
        for r in paged_rows:
            items.append({
                "id": r.get("id") or "1",
                "faculty_email": r.get("faculty_email") or "",
                "faculty_name": r.get("faculty_name") or "Faculty Member",
                "employee_id": r.get("employee_id"),
                "school": r.get("school"),
                "department": r.get("department"),
                "designation": r.get("designation"),
                "title": r.get("title") or "Untitled Book",
                "book": r.get("book"),
                "isbn": r.get("isbn"),
                "issn": r.get("issn"),
                "publisher": r.get("publisher"),
                "coauthor": r.get("coauthor"),
                "first_author": r.get("first_author"),
                "academic_year": r.get("academic_year"),
                "score": float(r.get("score") or 0.0),
                "hod_score": float(r.get("hod_score") or 0.0),
                "director_score": float(r.get("director_score") or 0.0),
                "dean_score": float(r.get("dean_score") or 0.0),
                "vc_score": float(r.get("vc_score") or 0.0),
                "final_validated_score": float(r.get("final_validated_score") or 0.0),
            })

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": ceil(total / page_size) if total else 0,
        }

    def faculty_detail(self, faculty_email: str) -> Dict[str, Any]:
        """Compute Detailed Books Analytics for a single faculty member."""
        clean_email = faculty_email.lower().strip()
        faculty_table = self._logical_table("faculty_profiles")

        fac_profile = {}
        if faculty_table is not None:
            fp_cols = SchemaReflector.column_names(faculty_table)
            fp_email_col = SchemaReflector.first_existing(fp_cols, EMAIL_COLUMNS) or "email"
            stmt = select(faculty_table).where(func.lower(func.trim(faculty_table.c[fp_email_col])) == clean_email)
            row = self.db.execute(stmt).mappings().first()
            if row:
                fac_profile = dict(row)

        filters = {"faculty_email": clean_email}
        all_records = self.records(1, 1000, filters)["items"]

        yearly_map: Dict[str, int] = {}
        pub_map: Dict[str, int] = {}
        total_score = 0.0
        total_vc_score = 0.0

        for r in all_records:
            year = str(r["academic_year"] or "Unknown")
            yearly_map[year] = yearly_map.get(year, 0) + 1

            pub = str(r["publisher"] or "Not Specified")
            pub_map[pub] = pub_map.get(pub, 0) + 1

            total_score += r["score"]
            total_vc_score += r["final_validated_score"]

        return {
            "faculty_profile": fac_profile or {"email": clean_email},
            "total_books": len(all_records),
            "books_by_academic_year": yearly_map,
            "publisher_distribution": pub_map,
            "records": all_records,
            "score_summary": {
                "self_score": round(total_score, 2),
                "final_validated_score": round(total_vc_score, 2),
            },
        }

    def export_csv_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return CSV export rows using current active filters."""
        return self.records(1, 10000, filters)["items"]

    def _get_filtered_joined_rows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        book_table = self._logical_table("book_publications")
        faculty_table = self._logical_table("faculty_profiles")

        if book_table is None or faculty_table is None:
            return []

        b_cols = SchemaReflector.column_names(book_table)
        fp_cols = SchemaReflector.column_names(faculty_table)

        b_email_col = SchemaReflector.first_existing(b_cols, ["faculty_email", "email"]) or "faculty_email"
        fp_email_col = SchemaReflector.first_existing(fp_cols, EMAIL_COLUMNS) or "email"

        b_title_col = SchemaReflector.first_existing(b_cols, ["title", "book_title", "paper_title"])
        b_book_col = SchemaReflector.first_existing(b_cols, ["book", "book_name", "volume_title"])
        b_pub_col = SchemaReflector.first_existing(b_cols, ["publisher", "publisher_name"])
        b_isbn_col = SchemaReflector.first_existing(b_cols, ["isbn", "isbn_no"])
        b_issn_col = SchemaReflector.first_existing(b_cols, ["issn", "issn_no"])
        b_role_col = SchemaReflector.first_existing(b_cols, ["role", "author_role"])
        b_first_col = SchemaReflector.first_existing(b_cols, ["first_author", "first_author_name"])
        b_co_col = SchemaReflector.first_existing(b_cols, ["coauthor", "co_authors"])
        b_year_col = SchemaReflector.first_existing(b_cols, YEAR_COLUMNS)

        fp_name_col = SchemaReflector.first_existing(fp_cols, NAME_COLUMNS) or "full_name"
        fp_emp_col = SchemaReflector.first_existing(fp_cols, EMPLOYEE_COLUMNS) or "employee_id"
        fp_school_col = SchemaReflector.first_existing(fp_cols, SCHOOL_COLUMNS) or "school"
        fp_dept_col = SchemaReflector.first_existing(fp_cols, DEPARTMENT_COLUMNS) or "department"
        fp_desig_col = SchemaReflector.first_existing(fp_cols, ["designation", "role"]) or "designation"

        self_col = SchemaReflector.first_existing(b_cols, ["score", "self_score"])
        hod_col = SchemaReflector.first_existing(b_cols, ["hod_score"])
        dir_col = SchemaReflector.first_existing(b_cols, ["director_score"])
        dean_col = SchemaReflector.first_existing(b_cols, ["dean_score"])
        vc_col = SchemaReflector.first_existing(b_cols, ["vc_score", "final_score"])

        join_cond = func.lower(func.trim(book_table.c[b_email_col])) == func.lower(func.trim(faculty_table.c[fp_email_col]))
        stmt = select(book_table, faculty_table).select_from(book_table.join(faculty_table, join_cond))

        # VALID BOOK CONDITION: NULLIF(TRIM(title), '') IS NOT NULL OR NULLIF(TRIM(book), '') IS NOT NULL
        title_conds = []
        if b_title_col and b_title_col in book_table.c:
            title_conds.append(and_(book_table.c[b_title_col].is_not(None), func.trim(book_table.c[b_title_col]) != ""))
        if b_book_col and b_book_col in book_table.c:
            title_conds.append(and_(book_table.c[b_book_col].is_not(None), func.trim(book_table.c[b_book_col]) != ""))

        if title_conds:
            clauses = [or_(*title_conds)]
        else:
            clauses = []

        if "is_active" in faculty_table.c:
            clauses.append(faculty_table.c.is_active == True)

        if filters.get("school") and fp_school_col in faculty_table.c:
            clauses.append(faculty_table.c[fp_school_col] == filters["school"])
        if filters.get("department") and fp_dept_col in faculty_table.c:
            clauses.append(faculty_table.c[fp_dept_col] == filters["department"])
        if filters.get("designation") and fp_desig_col in faculty_table.c:
            clauses.append(faculty_table.c[fp_desig_col] == filters["designation"])
        if filters.get("faculty_email") and fp_email_col in faculty_table.c:
            clauses.append(func.lower(func.trim(faculty_table.c[fp_email_col])) == str(filters["faculty_email"]).lower().strip())
        if filters.get("publisher") and b_pub_col in book_table.c:
            clauses.append(book_table.c[b_pub_col] == filters["publisher"])
        if filters.get("academic_year") and b_year_col in book_table.c:
            clauses.append(book_table.c[b_year_col].cast(String).contains(str(filters["academic_year"])))

        # ISBN status filter
        if filters.get("isbn_status") and b_isbn_col in book_table.c:
            status = str(filters["isbn_status"]).lower().strip()
            if status == "with_isbn":
                clauses.append(and_(book_table.c[b_isbn_col].is_not(None), func.trim(book_table.c[b_isbn_col]) != ""))
            elif status == "missing_isbn":
                clauses.append(or_(book_table.c[b_isbn_col].is_(None), func.trim(book_table.c[b_isbn_col]) == ""))

        stmt = stmt.where(and_(*clauses))

        output = []
        for r in self.db.execute(stmt).mappings():
            sc = float(r.get(self_col) or 0.0) if self_col and self_col in r else 0.0
            hod = float(r.get(hod_col) or 0.0) if hod_col and hod_col in r else 0.0
            direct = float(r.get(dir_col) or 0.0) if dir_col and dir_col in r else 0.0
            dn = float(r.get(dean_col) or 0.0) if dean_col and dean_col in r else 0.0
            vc = float(r.get(vc_col) or 0.0) if vc_col and vc_col in r else 0.0

            # Final validated score = COALESCE(vc_score, dean_score, director_score, hod_score, score, 0)
            final_val = vc if vc > 0 else (dn if dn > 0 else (direct if direct > 0 else (hod if hod > 0 else sc)))

            title_val = r.get(b_title_col) if b_title_col in r else None
            book_val = r.get(b_book_col) if b_book_col in r else None

            output.append({
                "id": r.get("id") or r.get("book_id") or 1,
                "faculty_email": r.get(fp_email_col) or r.get(b_email_col) or "",
                "faculty_name": r.get(fp_name_col) or "Faculty Member",
                "employee_id": r.get(fp_emp_col),
                "school": r.get(fp_school_col),
                "department": r.get(fp_dept_col),
                "designation": r.get(fp_desig_col),
                "title": title_val or book_val or "Untitled Book",
                "book": book_val,
                "isbn": r.get(b_isbn_col) if b_isbn_col in r else None,
                "issn": r.get(b_issn_col) if b_issn_col in r else None,
                "publisher": r.get(b_pub_col) if b_pub_col in r else None,
                "role": r.get(b_role_col) if b_role_col in r else None,
                "first_author": r.get(b_first_col) if b_first_col in r else None,
                "coauthor": r.get(b_co_col) if b_co_col in r else None,
                "academic_year": r.get(b_year_col) if b_year_col in r else None,
                "score": sc,
                "hod_score": hod,
                "director_score": direct,
                "dean_score": dn,
                "vc_score": vc,
                "final_validated_score": final_val,
            })

        return output

    def _logical_table(self, candidate_name: str) -> Optional[Table]:
        if candidate_name == "book_publications":
            candidates = ["book_publications", "books"]
        elif candidate_name == "faculty_profiles":
            candidates = ["faculty_profiles", "faculty", "users", "employees"]
        elif candidate_name == "journal_publications":
            candidates = ["journal_publications", "journals"]
        else:
            candidates = [candidate_name]

        resolved = self.reflector.resolve_table_name(candidates)
        return self.reflector.get_table(resolved) if resolved else None

    def _empty_overview(self, total_active_fac: int = 0) -> Dict[str, Any]:
        return {
            "total_book_publication_records": 0,
            "faculty_publishing_books": 0,
            "total_active_faculty": total_active_fac,
            "book_participation_rate": 0.0,
            "books_per_active_faculty": 0.0,
            "books_per_publishing_faculty": 0.0,
            "publications_with_isbn": 0,
            "isbn_completion_rate": 0.0,
            "first_author_contributions": 0,
            "coauthored_contributions": 0,
            "missing_isbn_count": 0,
            "duplicate_isbn_count": 0,
            "same_isbn_unrelated_titles_count": 0,
            "faculty_with_multiple_books": 0,
            "faculty_publishing_books_but_no_journals": 0,
            "faculty_publishing_both_books_and_journals": 0,
        }
