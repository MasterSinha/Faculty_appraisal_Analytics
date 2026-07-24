from typing import Any

from pydantic import BaseModel, Field


class ResearchOverview(BaseModel):
    total_active_faculty: int = 0
    total_journal_publications: int = 0
    faculty_with_journal_publication: int = 0
    publication_participation_rate: float = 0
    average_publications_per_publishing_faculty: float = 0
    total_book_publications: int = 0
    faculty_with_book_publication: int = 0
    total_patents: int = 0
    patents_granted: int = 0
    total_research_projects: int = 0
    total_sanctioned_funding: float = 0
    external_funded_projects: int = 0
    external_funded_amount: float = 0
    total_research_proposals: int = 0
    total_proposal_amount: float = 0
    total_research_scholars_guided: int = 0
    total_conferences: int = 0
    total_awards: int = 0
    total_products_developed: int = 0
    funding_per_active_faculty: float = 0


class PaginatedResponse(BaseModel):
    items: list[dict[str, Any]]
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0


class InsightResponse(BaseModel):
    insights: list[str] = Field(default_factory=list)

