from typing import Any, Dict, List, Optional
from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.orm import Session

from app.core.constants import (
    DEPARTMENT_COLUMNS,
    EMAIL_COLUMNS,
    EMPLOYEE_COLUMNS,
    FACULTY_LINK_COLUMNS,
    FACULTY_TABLES,
    NAME_COLUMNS,
    RESEARCH_TABLES,
    SCHOOL_COLUMNS,
)


class SchemaReflector:
    """Helper service to inspect and reflect live database table schemas."""

    def __init__(self, db: Session):
        self.db = db
        self.metadata = MetaData()
        self.inspector = inspect(db.bind)
        self.table_names = set(self.inspector.get_table_names())

    def resolve_table_name(self, candidates: List[str]) -> Optional[str]:
        lowered = {name.lower(): name for name in self.table_names}
        for candidate in candidates:
            if candidate.lower() in lowered:
                return lowered[candidate.lower()]
        return None

    def get_table(self, table_name: str) -> Table:
        return Table(table_name, self.metadata, autoload_with=self.db.bind)

    @staticmethod
    def column_names(table: Optional[Table]) -> List[str]:
        return list(table.c.keys()) if table is not None else []

    @staticmethod
    def first_existing(columns: List[str], candidates: List[str]) -> Optional[str]:
        lowered = {column.lower(): column for column in columns}
        for candidate in candidates:
            if candidate.lower() in lowered:
                return lowered[candidate.lower()]
        return None

    def inspect_full_schema(self) -> Dict[str, Any]:
        detected_tables = {}
        for logical_name, candidates in RESEARCH_TABLES.items():
            table_name = self.resolve_table_name(candidates)
            if not table_name:
                continue
            columns = self.column_names(self.get_table(table_name))
            detected_tables[logical_name] = {
                "table_name": table_name,
                "primary_keys": self.inspector.get_pk_constraint(table_name).get("constrained_columns", []),
                "foreign_keys": self.inspector.get_foreign_keys(table_name),
                "faculty_link_column": self.first_existing(columns, FACULTY_LINK_COLUMNS),
                "columns": columns,
            }

        faculty_table_name = self.resolve_table_name(FACULTY_TABLES)
        faculty_table = self.get_table(faculty_table_name) if faculty_table_name else None
        faculty_columns = self.column_names(faculty_table) if faculty_table is not None else []

        return {
            "faculty_table": {
                "table_name": faculty_table_name,
                "primary_keys": (
                    self.inspector.get_pk_constraint(faculty_table_name).get("constrained_columns", [])
                    if faculty_table_name
                    else []
                ),
                "name_column": self.first_existing(faculty_columns, NAME_COLUMNS),
                "email_column": self.first_existing(faculty_columns, EMAIL_COLUMNS),
                "employee_id_column": self.first_existing(faculty_columns, EMPLOYEE_COLUMNS),
                "school_column": self.first_existing(faculty_columns, SCHOOL_COLUMNS),
                "department_column": self.first_existing(faculty_columns, DEPARTMENT_COLUMNS),
                "columns": faculty_columns,
            },
            "research_tables": detected_tables,
        }
