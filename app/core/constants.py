from typing import Dict, List

RESEARCH_TABLES: Dict[str, List[str]] = {
    "journal_publications": ["journal_publications"],
    "book_publications": ["book_publications"],
    "conferences": ["conferences", "confrences"],
    "patents": ["patents"],
    "ipr_records": ["ipr_records"],
    "research_guidance": ["research_guidance"],
    "research_projects": ["research_projects"],
    "research_proposals": ["research_proposals"],
    "projects_guided": ["projects_guided"],
    "awards": ["awards"],
    "products_developed": ["products_developed"],
    "popular_writings": ["popular_writings"],
    "qualification_enhancement": ["qualification_enhancement"],
}

FACULTY_TABLES: List[str] = ["faculty", "users", "faculty_details", "employees", "user_profiles"]
FACULTY_LINK_COLUMNS: List[str] = ["faculty_id", "user_id", "employee_id", "appraisal_id", "submitted_by", "created_by"]
NAME_COLUMNS: List[str] = ["faculty_name", "name", "full_name", "employee_name", "first_name"]
EMAIL_COLUMNS: List[str] = ["email", "email_id", "official_email"]
EMPLOYEE_COLUMNS: List[str] = ["employee_id", "emp_id", "employee_code", "code"]
SCHOOL_COLUMNS: List[str] = ["school", "school_name", "school_id"]
DEPARTMENT_COLUMNS: List[str] = ["department", "department_name", "department_id"]
INDEXING_COLUMNS: List[str] = ["journal_indexing", "indexing", "indexed_in", "indexing_type"]
YEAR_COLUMNS: List[str] = ["publication_year", "year", "academic_year", "created_at", "publication_date", "date"]
VC_SCORE_COLUMNS: List[str] = ["vc_score", "vc_approved_score", "final_score"]
SELF_SCORE_COLUMNS: List[str] = ["self_score", "score"]
DIRECTOR_SCORE_COLUMNS: List[str] = ["director_score"]
DEAN_SCORE_COLUMNS: List[str] = ["dean_score"]
AMOUNT_COLUMNS: List[str] = ["amount", "sanctioned_amount", "funding_amount", "grant_amount"]
STATUS_COLUMNS: List[str] = ["project_status", "status"]
AGENCY_COLUMNS: List[str] = ["funding_agency", "agency", "sponsoring_agency"]
PROJECT_TYPE_COLUMNS: List[str] = ["project_type", "type"]
TITLE_COLUMNS: List[str] = ["title", "publication_title", "paper_title", "project_title", "journal_name"]

ALLOWED_ROLES = {"admin", "director", "dean", "registrar", "vc"}
