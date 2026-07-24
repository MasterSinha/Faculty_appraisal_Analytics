from math import ceil
from typing import Any, Dict, List, Optional

from sqlalchemy import Table, and_, distinct, func, literal, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.constants import (
    AGENCY_COLUMNS,
    AMOUNT_COLUMNS,
    DEAN_SCORE_COLUMNS,
    DEPARTMENT_COLUMNS,
    DIRECTOR_SCORE_COLUMNS,
    EMAIL_COLUMNS,
    EMPLOYEE_COLUMNS,
    FACULTY_LINK_COLUMNS,
    FACULTY_TABLES,
    INDEXING_COLUMNS,
    NAME_COLUMNS,
    PROJECT_TYPE_COLUMNS,
    RESEARCH_TABLES,
    SCHOOL_COLUMNS,
    SELF_SCORE_COLUMNS,
    STATUS_COLUMNS,
    VC_SCORE_COLUMNS,
    YEAR_COLUMNS,
)
from app.models.schema_reflector import SchemaReflector
from app.utils.indexing_normalizer import normalize_indexing


class AnalyticsSchemaError(RuntimeError):
    """Raised when an operation fails due to unexpected database schema mismatch."""
    pass


class ResearchAnalyticsRepository:
    """Repository executing database queries for faculty research analytics."""

    def __init__(self, db: Session):
        self.db = db
        self.reflector = SchemaReflector(db)

    def inspect_schema(self) -> Dict[str, Any]:
        return self.reflector.inspect_full_schema()

    def overview(self) -> Dict[str, Any]:
        faculty_table = self._faculty_table()
        faculty_pk = self._primary_key(faculty_table)
        journal = self._logical_table("journal_publications")
        projects = [self._logical_table("research_projects"), self._logical_table("research_proposals")]

        faculty_count = self._scalar(select(func.count(distinct(faculty_pk)))) if faculty_pk is not None else 0
        paper_count = self._count_rows(journal)
        faculty_with_research = self._distinct_faculty_count(journal)

        return {
            "total_faculty": faculty_count,
            "faculty_with_research": faculty_with_research,
            "total_research_papers": paper_count,
            "total_projects": sum(self._count_rows(table) for table in projects),
            "total_patents": self._count_rows(self._logical_table("patents")),
            "total_books": self._count_rows(self._logical_table("book_publications")),
            "total_conferences": self._count_rows(self._logical_table("conferences")),
            "total_funding": sum(self._sum_column(table, AMOUNT_COLUMNS) for table in projects),
            "total_vc_score": sum(
                self._sum_column(table, VC_SCORE_COLUMNS)
                for table in [journal, *projects, self._logical_table("book_publications")]
            ),
        }

    def indexing_distribution(self) -> List[Dict[str, Any]]:
        journal = self._logical_table("journal_publications")
        if journal is None:
            return []
        columns = SchemaReflector.column_names(journal)
        indexing_col = SchemaReflector.first_existing(columns, INDEXING_COLUMNS)
        faculty_col = SchemaReflector.first_existing(columns, FACULTY_LINK_COLUMNS)
        vc_col = SchemaReflector.first_existing(columns, VC_SCORE_COLUMNS)
        if indexing_col is None:
            return []

        statement = select(
            journal.c[indexing_col],
            func.count(),
            func.coalesce(func.sum(journal.c[vc_col]), 0) if vc_col else func.count(),
        )
        if faculty_col:
            statement = statement.add_columns(func.count(distinct(journal.c[faculty_col])))
        else:
            statement = statement.add_columns(func.count())
        statement = statement.group_by(journal.c[indexing_col])

        grouped: Dict[str, Dict[str, Any]] = {}
        for raw_indexing, papers, score, faculty_count in self.db.execute(statement).all():
            category = normalize_indexing(raw_indexing)
            item = grouped.setdefault(category, {"indexing": category, "total_papers": 0, "total_faculty": 0, "vc_score": 0.0})
            item["total_papers"] += int(papers or 0)
            item["total_faculty"] += int(faculty_count or 0)
            item["vc_score"] += float(score or 0)
        return list(grouped.values())

    def faculty_summary(self, page: int, page_size: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        faculty_table = self._faculty_table()
        faculty_pk = self._primary_key(faculty_table)
        if faculty_table is None or faculty_pk is None:
            return {"items": [], "page": page, "page_size": page_size, "total": 0, "total_pages": 0}

        faculty_rows = self._faculty_base_rows(faculty_table, faculty_pk, filters)
        summaries = {row["faculty_id"]: row for row in faculty_rows}

        journal_counts = self._aggregate_counts("journal_publications", filters)
        for faculty_id, row in journal_counts.items():
            if faculty_id in summaries:
                summaries[faculty_id].update(row)

        self._merge_simple_count(summaries, "book_publications", "book_publications")
        self._merge_simple_count(summaries, "conferences", "conference_publications")
        self._merge_simple_count(summaries, "patents", "patents")
        self._merge_project_counts(summaries)

        rows = list(summaries.values())
        rows = self._apply_search_sort(rows, filters)
        total = len(rows)
        start = (page - 1) * page_size
        return {
            "items": rows[start : start + page_size],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": ceil(total / page_size) if total else 0,
        }

    def faculty_detail(self, faculty_id: Any) -> Dict[str, Any]:
        summary = self.faculty_summary(1, 1, {"faculty_id": faculty_id})["items"]
        records = {}
        for logical_name in RESEARCH_TABLES:
            records[logical_name] = self._records_for_faculty(logical_name, faculty_id)
        return {
            "faculty": summary[0] if summary else {"faculty_id": faculty_id},
            "records": records,
            "score_summary": self.scores_comparison(faculty_id=faculty_id),
            "year_wise_activity_trend": self.publication_trend(faculty_id=faculty_id),
        }

    def publication_trend(self, faculty_id: Optional[Any] = None) -> List[Dict[str, Any]]:
        journal = self._logical_table("journal_publications")
        if journal is None:
            return []
        columns = SchemaReflector.column_names(journal)
        year_col = SchemaReflector.first_existing(columns, YEAR_COLUMNS)
        faculty_col = SchemaReflector.first_existing(columns, FACULTY_LINK_COLUMNS)
        if not year_col:
            return []
        year_expr = func.extract("year", journal.c[year_col]) if "date" in year_col or year_col.endswith("_at") else journal.c[year_col]
        statement = select(year_expr.label("year"), func.count().label("total")).group_by(year_expr).order_by(year_expr)
        if faculty_id is not None and faculty_col:
            statement = statement.where(journal.c[faculty_col] == faculty_id)

        results = []
        for row in self.db.execute(statement).all():
            if not row.year:
                continue
            try:
                raw_str = str(row.year).strip().split("-")[0].split("/")[0]
                cleaned_year = int(float(raw_str))
                if 1900 <= cleaned_year <= 2100:
                    results.append({"year": cleaned_year, "total_papers": int(row.total)})
            except (ValueError, TypeError):
                continue

        aggregated: Dict[int, int] = {}
        for item in results:
            aggregated[item["year"]] = aggregated.get(item["year"], 0) + item["total_papers"]

        return [{"year": y, "total_papers": aggregated[y]} for y in sorted(aggregated.keys())]

    def projects_summary(self) -> Dict[str, Any]:
        rows = []
        for logical_name in ("research_projects", "research_proposals"):
            table = self._logical_table(logical_name)
            if table is None:
                continue
            rows.extend(self._project_distribution(table))
        return {"data": rows}

    def scores_comparison(self, faculty_id: Optional[Any] = None) -> Dict[str, Any]:
        totals = {
            "self_score": 0.0,
            "director_score": 0.0,
            "dean_score": 0.0,
            "vc_score": 0.0,
            "reduced_by_director": 0,
            "reduced_by_dean": 0,
            "reduced_by_vc": 0,
            "unchanged_records": 0,
        }
        for logical_name in ("journal_publications", "research_projects", "research_proposals"):
            table = self._logical_table(logical_name)
            if table is None:
                continue
            columns = SchemaReflector.column_names(table)
            faculty_col = SchemaReflector.first_existing(columns, FACULTY_LINK_COLUMNS)
            self_col = SchemaReflector.first_existing(columns, SELF_SCORE_COLUMNS)
            director_col = SchemaReflector.first_existing(columns, DIRECTOR_SCORE_COLUMNS)
            dean_col = SchemaReflector.first_existing(columns, DEAN_SCORE_COLUMNS)
            vc_col = SchemaReflector.first_existing(columns, VC_SCORE_COLUMNS)
            statement = select(table)
            if faculty_id is not None and faculty_col:
                statement = statement.where(table.c[faculty_col] == faculty_id)
            for row in self.db.execute(statement).mappings():
                values = {
                    "self_score": float(row.get(self_col) or 0) if self_col else 0.0,
                    "director_score": float(row.get(director_col) or 0) if director_col else 0.0,
                    "dean_score": float(row.get(dean_col) or 0) if dean_col else 0.0,
                    "vc_score": float(row.get(vc_col) or 0) if vc_col else 0.0,
                }
                for key, value in values.items():
                    totals[key] += value
                totals["reduced_by_director"] += int(values["director_score"] < values["self_score"])
                totals["reduced_by_dean"] += int(values["dean_score"] < values["director_score"])
                totals["reduced_by_vc"] += int(values["vc_score"] < values["dean_score"])
                totals["unchanged_records"] += int(len(set(values.values())) == 1)
        return totals

    def top_faculty(self, limit: int) -> List[Dict[str, Any]]:
        data = self.faculty_summary(1, limit, {"sort_by": "total_research_papers", "sort_order": "desc"})
        return data["items"]

    def top_journals(self, limit: int = 10) -> List[Dict[str, Any]]:
        journal = self._logical_table("journal_publications")
        if journal is None:
            return []
        columns = SchemaReflector.column_names(journal)
        title_col = SchemaReflector.first_existing(columns, ["journal_name", "journal", "name", "publication_name"])
        if not title_col:
            return []
        statement = (
            select(journal.c[title_col].label("journal"), func.count().label("total"))
            .group_by(journal.c[title_col])
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [{"journal": row.journal or "Not specified", "total": int(row.total)} for row in self.db.execute(statement).all()]

    def filters(self) -> Dict[str, Any]:
        faculty_table = self._faculty_table()
        faculty_columns = SchemaReflector.column_names(faculty_table)
        school_col = SchemaReflector.first_existing(faculty_columns, SCHOOL_COLUMNS)
        dept_col = SchemaReflector.first_existing(faculty_columns, DEPARTMENT_COLUMNS)
        project = self._logical_table("research_projects")
        project_columns = SchemaReflector.column_names(project)

        try:
            years = [row["year"] for row in self.publication_trend()]
        except Exception:
            years = []

        try:
            indexing_cats = [row["indexing"] for row in self.indexing_distribution()]
        except Exception:
            indexing_cats = []

        return {
            "schools": self._distinct_values(faculty_table, school_col),
            "departments": self._distinct_values(faculty_table, dept_col),
            "years": years,
            "indexing_categories": indexing_cats,
            "project_statuses": self._distinct_values(project, SchemaReflector.first_existing(project_columns, STATUS_COLUMNS)),
            "funding_agencies": self._distinct_values(project, SchemaReflector.first_existing(project_columns, AGENCY_COLUMNS)),
        }

    def _faculty_base_rows(self, table: Table, faculty_pk: Any, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        columns = SchemaReflector.column_names(table)
        name_col = SchemaReflector.first_existing(columns, NAME_COLUMNS)
        email_col = SchemaReflector.first_existing(columns, EMAIL_COLUMNS)
        employee_col = SchemaReflector.first_existing(columns, EMPLOYEE_COLUMNS)
        school_col = SchemaReflector.first_existing(columns, SCHOOL_COLUMNS)
        dept_col = SchemaReflector.first_existing(columns, DEPARTMENT_COLUMNS)
        statement = select(table)
        clauses = []
        if filters.get("faculty_id") is not None:
            clauses.append(faculty_pk == filters["faculty_id"])
        if filters.get("school") and school_col:
            clauses.append(table.c[school_col] == filters["school"])
        if filters.get("department") and dept_col:
            clauses.append(table.c[dept_col] == filters["department"])
        if clauses:
            statement = statement.where(and_(*clauses))

        rows = []
        for row in self.db.execute(statement).mappings():
            name = row.get(name_col) if name_col else None
            rows.append({
                "faculty_id": row.get(faculty_pk.name),
                "faculty_name": str(name or "Unknown faculty"),
                "employee_id": row.get(employee_col) if employee_col else None,
                "email": row.get(email_col) if email_col else None,
                "school": row.get(school_col) if school_col else None,
                "department": row.get(dept_col) if dept_col else None,
                "total_research_papers": 0,
                "sci_papers": 0,
                "scopus_papers": 0,
                "ugc_papers": 0,
                "other_indexed_papers": 0,
                "book_publications": 0,
                "conference_publications": 0,
                "patents": 0,
                "research_projects": 0,
                "total_funding": 0.0,
                "total_vc_score": 0.0,
            })
        return rows

    def _aggregate_counts(self, logical_name: str, filters: Dict[str, Any]) -> Dict[Any, Dict[str, Any]]:
        table = self._logical_table(logical_name)
        if table is None:
            return {}
        columns = SchemaReflector.column_names(table)
        faculty_col = SchemaReflector.first_existing(columns, FACULTY_LINK_COLUMNS)
        indexing_col = SchemaReflector.first_existing(columns, INDEXING_COLUMNS)
        vc_col = SchemaReflector.first_existing(columns, VC_SCORE_COLUMNS)
        if not faculty_col:
            return {}
        statement = select(
            table.c[faculty_col],
            table.c[indexing_col] if indexing_col else literal(None),
            table.c[vc_col] if vc_col else literal(0),
        )
        result = {}
        for faculty_id, indexing, vc_score in self.db.execute(statement).all():
            row = result.setdefault(
                faculty_id,
                {"total_research_papers": 0, "sci_papers": 0, "scopus_papers": 0, "ugc_papers": 0, "other_indexed_papers": 0, "total_vc_score": 0.0},
            )
            row["total_research_papers"] += 1
            category = normalize_indexing(indexing if indexing_col else None)
            if category == "SCI / Web of Science":
                row["sci_papers"] += 1
            elif category == "Scopus":
                row["scopus_papers"] += 1
            elif category == "UGC":
                row["ugc_papers"] += 1
            else:
                row["other_indexed_papers"] += 1
            row["total_vc_score"] += float(vc_score or 0) if vc_col else 0.0
        return result

    def _merge_simple_count(self, summaries: Dict[Any, Dict[str, Any]], logical_name: str, target_key: str) -> None:
        table = self._logical_table(logical_name)
        if table is None:
            return
        columns = SchemaReflector.column_names(table)
        faculty_col = SchemaReflector.first_existing(columns, FACULTY_LINK_COLUMNS)
        if not faculty_col:
            return
        statement = select(table.c[faculty_col], func.count()).group_by(table.c[faculty_col])
        for faculty_id, total in self.db.execute(statement).all():
            if faculty_id in summaries:
                summaries[faculty_id][target_key] = int(total or 0)

    def _merge_project_counts(self, summaries: Dict[Any, Dict[str, Any]]) -> None:
        for logical_name in ("research_projects", "research_proposals"):
            table = self._logical_table(logical_name)
            if table is None:
                continue
            columns = SchemaReflector.column_names(table)
            faculty_col = SchemaReflector.first_existing(columns, FACULTY_LINK_COLUMNS)
            amount_col = SchemaReflector.first_existing(columns, AMOUNT_COLUMNS)
            type_col = SchemaReflector.first_existing(columns, PROJECT_TYPE_COLUMNS)
            if not faculty_col:
                continue
            for row in self.db.execute(select(table)).mappings():
                faculty_id = row.get(faculty_col)
                if faculty_id not in summaries:
                    continue
                summaries[faculty_id]["research_projects"] += 1
                summaries[faculty_id]["total_funding"] += float(row.get(amount_col) or 0) if amount_col else 0.0
                project_type = str(row.get(type_col) or "").lower() if type_col else ""
                summaries[faculty_id]["internal_projects"] = summaries[faculty_id].get("internal_projects", 0) + int("internal" in project_type)
                summaries[faculty_id]["external_projects"] = summaries[faculty_id].get("external_projects", 0) + int("external" in project_type)

    def _records_for_faculty(self, logical_name: str, faculty_id: Any) -> List[Dict[str, Any]]:
        table = self._logical_table(logical_name)
        if table is None:
            return []
        columns = SchemaReflector.column_names(table)
        faculty_col = SchemaReflector.first_existing(columns, FACULTY_LINK_COLUMNS)
        if not faculty_col:
            return []
        statement = select(table).where(table.c[faculty_col] == faculty_id).limit(200)
        return [dict(row) for row in self.db.execute(statement).mappings()]

    def _project_distribution(self, table: Table) -> List[Dict[str, Any]]:
        columns = SchemaReflector.column_names(table)
        status_col = SchemaReflector.first_existing(columns, STATUS_COLUMNS)
        agency_col = SchemaReflector.first_existing(columns, AGENCY_COLUMNS)
        amount_col = SchemaReflector.first_existing(columns, AMOUNT_COLUMNS)
        type_col = SchemaReflector.first_existing(columns, PROJECT_TYPE_COLUMNS)
        rows = []
        for column, label in ((status_col, "status"), (agency_col, "funding_agency"), (type_col, "project_type")):
            if not column:
                continue
            amount_expr = func.coalesce(func.sum(table.c[amount_col]), 0) if amount_col else func.count()
            statement = select(table.c[column].label("name"), func.count().label("total"), amount_expr.label("amount")).group_by(table.c[column])
            rows.extend({"group": label, "name": row.name or "Not specified", "total": int(row.total), "amount": float(row.amount or 0)} for row in self.db.execute(statement).all())
        return rows

    def _apply_search_sort(self, rows: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        search = (filters.get("search") or "").lower()
        if search:
            rows = [
                row for row in rows
                if search in str(row.get("faculty_name", "")).lower() or search in str(row.get("employee_id", "")).lower()
            ]
        sort_by = filters.get("sort_by") or "total_research_papers"
        reverse = (filters.get("sort_order") or "desc").lower() == "desc"
        return sorted(rows, key=lambda row: row.get(sort_by) or 0, reverse=reverse)

    def _logical_table(self, logical_name: str) -> Optional[Table]:
        table_name = self.reflector.resolve_table_name(RESEARCH_TABLES[logical_name])
        return self.reflector.get_table(table_name) if table_name else None

    def _faculty_table(self) -> Optional[Table]:
        table_name = self.reflector.resolve_table_name(FACULTY_TABLES)
        return self.reflector.get_table(table_name) if table_name else None

    def _primary_key(self, table: Optional[Table]) -> Optional[Any]:
        if table is None:
            return None
        primary_keys = list(table.primary_key.columns)
        if primary_keys:
            return primary_keys[0]
        for candidate in ("id", "faculty_id", "user_id", "employee_id"):
            if candidate in table.c:
                return table.c[candidate]
        return None

    def _count_rows(self, table: Optional[Table]) -> int:
        if table is None:
            return 0
        return int(self._scalar(select(func.count()).select_from(table)) or 0)

    def _distinct_faculty_count(self, table: Optional[Table]) -> int:
        if table is None:
            return 0
        faculty_col = SchemaReflector.first_existing(SchemaReflector.column_names(table), FACULTY_LINK_COLUMNS)
        if not faculty_col:
            return 0
        return int(self._scalar(select(func.count(distinct(table.c[faculty_col])))) or 0)

    def _sum_column(self, table: Optional[Table], candidates: List[str]) -> float:
        if table is None:
            return 0.0
        column = SchemaReflector.first_existing(SchemaReflector.column_names(table), candidates)
        if not column:
            return 0.0
        return float(self._scalar(select(func.coalesce(func.sum(table.c[column]), 0))) or 0)

    def _distinct_values(self, table: Optional[Table], column: Optional[str]) -> List[Any]:
        if table is None or not column:
            return []
        statement = select(distinct(table.c[column])).where(table.c[column].is_not(None)).order_by(table.c[column])
        return [row[0] for row in self.db.execute(statement).all() if row[0] not in ("", None)]

    def _scalar(self, statement: Any) -> Any:
        try:
            return self.db.execute(statement).scalar()
        except SQLAlchemyError as exc:
            raise AnalyticsSchemaError("Unable to read analytics data from the configured database.") from exc
