from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BookOverviewResponse(BaseModel):
    total_book_publication_records: int = Field(0, description="Total valid book publication records")
    faculty_publishing_books: int = Field(0, description="Count of distinct active faculty with valid books")
    total_active_faculty: int = Field(0, description="Total active faculty in selected scope")
    book_participation_rate: float = Field(0.0, description="Percentage of active faculty publishing books")
    books_per_active_faculty: float = Field(0.0, description="Total books divided by total active faculty")
    books_per_publishing_faculty: float = Field(0.0, description="Total books divided by publishing faculty")
    publications_with_isbn: int = Field(0, description="Count of book records with valid ISBN")
    isbn_completion_rate: float = Field(0.0, description="Percentage of books with ISBN registered")
    first_author_contributions: int = Field(0, description="First author contribution count")
    coauthored_contributions: int = Field(0, description="Co-authored contribution count")
    missing_isbn_count: int = Field(0, description="Count of book records missing ISBN")
    duplicate_isbn_count: int = Field(0, description="Count of ISBNs appearing more than once")
    same_isbn_unrelated_titles_count: int = Field(0, description="Count of same ISBN used across different titles")
    faculty_with_multiple_books: int = Field(0, description="Faculty with 2 or more books")
    faculty_publishing_books_but_no_journals: int = Field(0, description="Faculty publishing books but zero journals")
    faculty_publishing_both_books_and_journals: int = Field(0, description="Faculty publishing both books and journals")


class DepartmentBookAnalyticsItem(BaseModel):
    school: Optional[str] = Field(None, description="School name")
    department: str = Field(..., description="Department name")
    active_faculty: int = Field(0, description="Total active faculty in department")
    total_book_publications: int = Field(0, description="Total valid book publications in department")
    faculty_publishing_books: int = Field(0, description="Publishing faculty count in department")
    book_participation_rate: float = Field(0.0, description="Participation rate (%)")
    books_per_active_faculty: float = Field(0.0, description="Books per active faculty")
    books_per_publishing_faculty: float = Field(0.0, description="Books per publishing faculty")
    publications_with_isbn: int = Field(0, description="Book count with ISBN")
    isbn_completion_rate: float = Field(0.0, description="ISBN completion rate (%)")
    first_author_contributions: int = Field(0, description="First author records")
    coauthored_contributions: int = Field(0, description="Co-authored records")
    total_score: float = Field(0.0, description="Aggregate self score")
    final_validated_score: float = Field(0.0, description="Aggregate validated VC score")


class PaginatedDepartmentBookResponse(BaseModel):
    items: List[DepartmentBookAnalyticsItem] = Field(default_factory=list)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    total: int = Field(0, ge=0)
    total_pages: int = Field(0, ge=0)


class PublisherAnalyticsItem(BaseModel):
    publisher: str = Field(..., description="Publisher name")
    total_books: int = Field(0, description="Total books published")
    faculty_count: int = Field(0, description="Distinct faculty count")
    isbn_count: int = Field(0, description="Books with registered ISBN")
    average_score: float = Field(0.0, description="Average final validated score")


class FacultyAuthorContribution(BaseModel):
    faculty_email: str = Field(..., description="Faculty email")
    faculty_name: str = Field(..., description="Faculty full name")
    count: int = Field(0, description="Contribution count")


class AuthorshipAnalyticsResponse(BaseModel):
    first_author_contributions: int = Field(0, description="Total first author contributions")
    coauthored_contributions: int = Field(0, description="Total co-authored contributions")
    unspecified_authorship: int = Field(0, description="Records with unspecified author role")
    faculty_with_multiple_books: int = Field(0, description="Faculty with 2+ books")
    top_first_author_faculty: List[FacultyAuthorContribution] = Field(default_factory=list)
    top_coauthor_faculty: List[FacultyAuthorContribution] = Field(default_factory=list)


class DuplicateIsbnRecord(BaseModel):
    isbn: str = Field(..., description="Duplicate ISBN string")
    count: int = Field(0, description="Total occurrences")
    titles: List[str] = Field(default_factory=list, description="List of book titles sharing this ISBN")


class QualityAnalyticsResponse(BaseModel):
    missing_isbn_count: int = Field(0, description="Records missing ISBN")
    duplicate_isbn_count: int = Field(0, description="Count of duplicate ISBN strings")
    same_isbn_unrelated_titles_count: int = Field(0, description="ISBNs shared across different titles")
    missing_publisher_count: int = Field(0, description="Records missing publisher")
    missing_title_and_book_count: int = Field(0, description="Records missing title/book name")
    isbn_completion_rate: float = Field(0.0, description="ISBN completion percentage")
    most_common_publishers: List[PublisherAnalyticsItem] = Field(default_factory=list)
    duplicate_isbn_records: List[DuplicateIsbnRecord] = Field(default_factory=list)


class BookRecordItem(BaseModel):
    id: Any = Field(..., description="Book publication ID")
    faculty_email: str = Field(..., description="Faculty email address")
    faculty_name: str = Field("Faculty Member", description="Faculty full name")
    employee_id: Optional[str] = Field(None, description="Employee ID")
    school: Optional[str] = Field(None, description="School name")
    department: Optional[str] = Field(None, description="Department name")
    designation: Optional[str] = Field(None, description="Faculty designation")
    title: str = Field("Untitled Book", description="Book or chapter title")
    book: Optional[str] = Field(None, description="Book name / volume title")
    isbn: Optional[str] = Field(None, description="ISBN number")
    issn: Optional[str] = Field(None, description="ISSN number if applicable")
    publisher: Optional[str] = Field(None, description="Publisher name")
    coauthor: Optional[str] = Field(None, description="Co-author details")
    first_author: Optional[str] = Field(None, description="First author details")
    academic_year: Optional[str] = Field(None, description="Publication academic year")
    score: float = Field(0.0, description="Self reported score")
    hod_score: float = Field(0.0, description="HOD score")
    director_score: float = Field(0.0, description="Director score")
    dean_score: float = Field(0.0, description="Dean score")
    vc_score: float = Field(0.0, description="VC score")
    final_validated_score: float = Field(0.0, description="COALESCE(vc_score, dean_score, director_score, hod_score, score, 0)")


class PaginatedBookRecordResponse(BaseModel):
    items: List[BookRecordItem] = Field(default_factory=list)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    total: int = Field(0, ge=0)
    total_pages: int = Field(0, ge=0)


class FacultyBookDetailResponse(BaseModel):
    faculty_profile: Dict[str, Any] = Field(default_factory=dict, description="Faculty details")
    total_books: int = Field(0, description="Total valid books published")
    books_by_academic_year: Dict[str, int] = Field(default_factory=dict, description="Yearly book count breakdown")
    publisher_distribution: Dict[str, int] = Field(default_factory=dict, description="Publisher distribution")
    records: List[BookRecordItem] = Field(default_factory=list, description="List of book publication records")
    score_summary: Dict[str, float] = Field(default_factory=dict, description="Self and validated score totals")
