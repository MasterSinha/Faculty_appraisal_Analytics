"""
Faculty Research Analytics Deduplication Utilities
Implements normalized deduplication identity keys, grouped record generation,
and metrics (raw submissions vs distinct outputs vs distinct faculty credits).
"""

from math import ceil
from typing import Any, Dict, List, Optional, Set, Tuple


def safe_clean(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip().lower()


def get_journal_dedupe_key(row: Dict[str, Any]) -> str:
    if not row:
        return "unknown_title|unknown_journal|no_issn|unknown_year"
    title = safe_clean(row.get("title") or row.get("paper_title"))
    if not title:
        title = "unknown_title"
    journal = safe_clean(row.get("journal") or row.get("journal_name"))
    issn_raw = safe_clean(row.get("issn") or row.get("issn_no") or row.get("e_issn"))
    if not issn_raw or issn_raw in ("none", "n/a", "na", "null", "-", "none/blank"):
        issn_val = "no_issn"
    else:
        issn_val = issn_raw
    year = safe_clean(row.get("academic_year") or row.get("year")) or "unknown_year"
    return f"{title}|{journal}|{issn_val}|{year}"


def get_patent_dedupe_key(row: Dict[str, Any]) -> str:
    if not row:
        return "file_no:none"
    file_no = safe_clean(
        row.get("file_number")
        or row.get("file_no")
        or row.get("patent_number")
        or row.get("application_number")
        or row.get("sanction_order_number")
    )
    if file_no and file_no not in ("none", "n/a", "na", "null", "-"):
        return f"file_no:{file_no}"
    title = safe_clean(row.get("title") or row.get("patent_title")) or "unknown_title"
    year = safe_clean(row.get("academic_year") or row.get("year")) or "unknown_year"
    return f"title:{title}|{year}"


def get_book_dedupe_key(row: Dict[str, Any]) -> str:
    if not row:
        return "unknown_title|no_isbn|unknown_year"
    title = safe_clean(row.get("title") or row.get("book") or row.get("book_title")) or "unknown_title"
    isbn_raw = safe_clean(row.get("isbn"))
    if not isbn_raw or isbn_raw in ("none", "n/a", "na", "null", "-"):
        isbn_val = "no_isbn"
    else:
        isbn_val = isbn_raw
    year = safe_clean(row.get("academic_year") or row.get("year")) or "unknown_year"
    return f"{title}|{isbn_val}|{year}"


def get_ipr_dedupe_key(row: Dict[str, Any]) -> str:
    if not row:
        return "unknown_title|unknown_year"
    title = safe_clean(row.get("title") or row.get("details")) or "unknown_title"
    year = safe_clean(row.get("academic_year") or row.get("year")) or "unknown_year"
    return f"{title}|{year}"


def get_project_dedupe_key(row: Dict[str, Any]) -> str:
    if not row:
        return "sanction:none"
    file_no = safe_clean(
        row.get("sanction_order_number")
        or row.get("sanction_number")
        or row.get("file_number")
        or row.get("file_no")
        or row.get("project_code")
        or row.get("project_id")
    )
    if file_no and file_no not in ("none", "n/a", "na", "null", "-"):
        return f"sanction:{file_no}"
    title = safe_clean(row.get("title") or row.get("project_title")) or "unknown_title"
    amount = str(row.get("amount") or 0)
    agency = safe_clean(row.get("agency") or row.get("funding_agency"))
    return f"title:{title}|{amount}|{agency}"


def get_document_dedupe_key(row: Dict[str, Any]) -> str:
    if not row:
        return "file:unknown|0"
    file_hash = safe_clean(row.get("file_hash") or row.get("hash"))
    if file_hash and file_hash not in ("none", "n/a", "na", "null", "-"):
        return f"hash:{file_hash}"
    doc_key = safe_clean(row.get("doc_key") or row.get("document_key"))
    if doc_key and doc_key not in ("none", "n/a", "na", "null", "-"):
        return f"dockey:{doc_key}"
    filename = safe_clean(row.get("original_filename") or row.get("filename") or row.get("title")) or "unknown"
    size = str(row.get("file_size") or row.get("size") or "0")
    return f"file:{filename}|{size}"


def normalize_patent_status(status_str: Optional[str]) -> str:
    if not status_str:
        return "Pending"
    s_lower = str(status_str).strip().lower()
    if "grant" in s_lower:
        return "Granted"
    if "file" in s_lower or "submit" in s_lower or "process" in s_lower or "pend" in s_lower or "publish" in s_lower:
        return "Pending"
    return "Pending"


def sort_key_representative(r: Dict[str, Any]):
    upd = str(r.get("updated_at") or "")
    cre = str(r.get("created_at") or "")
    row_id = 0
    try:
        row_id = int(r.get("id") or 0)
    except Exception:
        row_id = 0
    return (upd, cre, row_id)


def group_records_by_key(
    rows: List[Dict[str, Any]],
    key_fn,
    category_name: str = "publication"
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Groups raw filtered records by deduplication key and returns:
    1. List of grouped records formatted for frontend (with contributor details, counts, dedupe_key, representative row).
    2. Summary dictionary containing raw count, grouped count, distinct credits, duplicate groups count, duplicate rows removed.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        k = key_fn(r)
        groups.setdefault(k, []).append(r)

    raw_filtered_count = len(rows)
    grouped_filtered_count = len(groups)
    faculty_credits_set: Set[Tuple[str, str]] = set()

    for k, group_rows in groups.items():
        for r in group_rows:
            f_email = safe_clean(r.get("faculty_email") or r.get("email"))
            if f_email:
                faculty_credits_set.add((f_email, k))

    total_distinct_faculty_credits = len(faculty_credits_set)
    duplicate_groups_count = sum(
        1 for g in groups.values()
        if len(g) > 1 or len({safe_clean(r.get("faculty_email") or r.get("email")) for r in g if safe_clean(r.get("faculty_email") or r.get("email"))}) > 1
    )
    duplicate_rows_removed = raw_filtered_count - grouped_filtered_count

    grouped_items = []
    for k, group_rows in groups.items():
        # Representative row selection: newest updated_at, fallback created_at, fallback highest id
        sorted_group_rows = sorted(group_rows, key=sort_key_representative, reverse=True)
        representative = sorted_group_rows[0]
        rec_count = len(group_rows)

        # Build unique contributors list by normalized faculty_email
        contrib_map: Dict[str, Dict[str, Any]] = {}
        for r in group_rows:
            fe = safe_clean(r.get("faculty_email") or r.get("email"))
            if fe and fe not in contrib_map:
                contrib_map[fe] = {
                    "faculty_name": r.get("faculty_name") or r.get("full_name") or fe,
                    "faculty_email": fe,
                    "department": r.get("department") or "",
                    "school": r.get("school") or "",
                    "designation": r.get("designation") or "",
                }
        contributors = list(contrib_map.values())
        fac_count = len(contributors)

        # Base dict from representative row
        grouped_dict = dict(representative)
        grouped_dict["dedupe_key"] = k
        grouped_dict["title"] = representative.get("title") or representative.get("paper_title") or representative.get("book") or representative.get("patent_title") or ""
        grouped_dict["academic_year"] = representative.get("academic_year") or ""
        grouped_dict["record_count"] = rec_count
        grouped_dict["faculty_count"] = fac_count
        grouped_dict["contributors"] = contributors
        grouped_dict["is_duplicate_group"] = (rec_count > 1 or fac_count > 1)

        # Special normalization by category
        if category_name in ("patent", "patents"):
            grouped_dict["patent_title"] = representative.get("patent_title") or representative.get("title") or ""
            grouped_dict["file_number"] = representative.get("file_number") or representative.get("file_no") or representative.get("patent_number") or ""
            grouped_dict["status"] = normalize_patent_status(representative.get("patent_status") or representative.get("status"))

        # Best score in group
        scores = [float(r.get("final_validated_score") or r.get("score") or 0.0) for r in group_rows]
        grouped_dict["final_validated_score"] = max(scores) if scores else 0.0

        grouped_items.append(grouped_dict)

    cat_prefix = category_name.rstrip("s")
    metrics_summary = {
        f"total_{cat_prefix}_submissions_raw": raw_filtered_count,
        f"total_distinct_{cat_prefix}s": grouped_filtered_count,
        f"total_distinct_faculty_{cat_prefix}_credits": total_distinct_faculty_credits,
        f"duplicate_{cat_prefix}_groups": duplicate_groups_count,
        f"duplicate_{cat_prefix}_rows": duplicate_rows_removed,
        "raw_filtered_count": raw_filtered_count,
        "grouped_filtered_count": grouped_filtered_count,
        "duplicate_groups_count": duplicate_groups_count,
        "duplicate_rows_removed": duplicate_rows_removed,
    }

    return grouped_items, metrics_summary
