import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.repositories.innovation_pipeline_analytics_repository import InnovationPipelineAnalyticsRepository

logger = logging.getLogger(__name__)


class InnovationPipelineAnalyticsService:
    """Service layer for Innovation Pipeline Analytics with robust error resilience."""

    def __init__(self, db: Session):
        self.repository = InnovationPipelineAnalyticsRepository(db)

    def get_analytics(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.repository.get_analytics(filters)
        except Exception as exc:
            logger.exception("Error during Innovation Pipeline Analytics retrieval: %s", exc)
            return {
                "research_proposals": [],
                "research_projects": [],
                "external_research_projects": [],
                "patents": [],
                "ipr_records": [],
                "products_developed": [],
                "summary": {
                    "proposals_submitted": 0,
                    "projects_sanctioned": 0,
                    "patent_or_ipr_records": 0,
                    "patents_granted": 0,
                    "products_developed": 0,
                    "innovation_active_faculty": 0,
                    "limitation_note": "Pipeline stages represent aggregate institutional counts. Existing database records do not contain a shared innovation identifier, so individual proposals cannot be followed reliably through every stage.",
                    "aggregate_funnel": [],
                    "pipeline_stages_by_department": [],
                    "innovation_activity_by_school": [],
                    "academic_year_pipeline_trend": [],
                    "faculty_innovation_diversity": [],
                },
                "department_contribution": [],
                "school_contribution": [],
                "academic_year_comparison": [],
                "faculty_innovation_diversity": [],
                "gap_analytics": {
                    "proposals_without_corresponding_aggregate_project_activity": 0,
                    "departments_with_projects_but_no_patents": [],
                    "faculty_with_patents_but_no_products": [],
                    "departments_with_no_products_developed": [],
                    "schools_with_no_external_projects": [],
                    "faculty_active_in_three_or_more_innovation_categories": [],
                    "departments_showing_strong_project_funding_but_weak_product_output": [],
                },
            }
