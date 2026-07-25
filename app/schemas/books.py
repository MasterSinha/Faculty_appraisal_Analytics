from typing import Any, List, Optional
from pydantic import BaseModel, Field


class BookKpiResponse(BaseModel):
    total_books: int = Field(0, description="Total valid book publications and chapters")
    publishing_faculty: int = Field(0, description="Distinct count of active faculty who published books")
    total_active_faculty: int = Field(0, description="Total count of active faculty profiles")
    participation_rate: float = Field(0.0, description="Percentage of active faculty publishing books")
    books_per_active_faculty: float = Field(0.0, description="Average books per active faculty member")
    books_per_publishing_faculty: float = Field(0.0, description="Average books per publishing faculty member")
    isbn_count: int = Field(0, description="Books with valid ISBN registered")
    first_author_count: int = Field(0, description="First-author publication records")
    co_author_count: int = Field(0, description="Co-authored publication records")


class BookChartItem(BaseModel):
    name: str = Field(..., description="Category label (e.g. department, publisher, year, role)")
    total: int = Field(0, description="Book count")
    percentage: float = Field(0.0, description="Percentage share")


class BookChartsResponse(BaseModel):
    by_department: List[BookChartItem] = Field(default_factory=list)
    by_publisher: List[BookChartItem] = Field(default_factory=list)
    by_role: List[BookChartItem] = Field(default_factory=list)
    by_year: List[BookChartItem] = Field(default_factory=list)


class BookQuadrantItem(BaseModel):
    department: str = Field(..., description="Department name")
    school: Optional[str] = Field(None, description="School name")
    total_active_faculty: int = Field(0, description="Total active faculty count")
    publishing_faculty_count: int = Field(0, description="Publishing faculty count")
    total_books: int = Field(0, description="Total book count")
    participation_rate: float = Field(0.0, description="X-axis: Participation rate (%)")
    books_per_active_faculty: float = Field(0.0, description="Y-axis: Books per active faculty")
    quadrant: str = Field(..., description="Quadrant classification label")


class BookTableItem(BaseModel):
    id: Any = Field(..., description="Book publication ID")
    faculty_email: str = Field(..., description="Faculty email address")
    faculty_name: str = Field("Unknown faculty", description="Faculty full name")
    employee_id: Optional[str] = Field(None, description="Employee ID")
    school: Optional[str] = Field(None, description="School name")
    department: Optional[str] = Field(None, description="Department name")
    book_title: str = Field("Untitled Book", description="Book or chapter title")
    publisher: Optional[str] = Field(None, description="Publisher name")
    isbn: Optional[str] = Field(None, description="ISBN code")
    role: Optional[str] = Field(None, description="Author role (First Author, Co-Author, Editor)")
    academic_year: Optional[str] = Field(None, description="Publication academic year")
    self_score: float = Field(0.0, description="Self reported score")
    vc_score: float = Field(0.0, description="Final validated VC score")


class PaginatedBookResponse(BaseModel):
    items: List[BookTableItem] = Field(default_factory=list)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    total: int = Field(0, ge=0)
    total_pages: int = Field(0, ge=0)


class IndexRecommendationResponse(BaseModel):
    recommended_indexes: List[str] = Field(default_factory=list, description="Recommended SQL DDL index creation statements")
