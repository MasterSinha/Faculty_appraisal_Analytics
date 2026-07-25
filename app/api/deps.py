from typing import Generator
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_analytics_role
from app.database import get_db
from app.services.appraisal_completion_analytics_service import AppraisalCompletionAnalyticsService
from app.services.books_analytics_service import BooksAnalyticsService
from app.services.conferences_awards_analytics_service import ConferencesAwardsAnalyticsService
from app.services.department_performance_analytics_service import DepartmentPerformanceAnalyticsService
from app.services.faculty_performance_analytics_service import FacultyPerformanceAnalyticsService
from app.services.faculty_research_analytics_service import FacultyResearchAnalyticsService
from app.services.innovation_pipeline_analytics_service import InnovationPipelineAnalyticsService
from app.services.journals_analytics_service import JournalsAnalyticsService
from app.services.patents_analytics_service import PatentsAnalyticsService
from app.services.projects_funding_analytics_service import ProjectsFundingAnalyticsService
from app.services.research_analytics_service import ResearchAnalyticsService
from app.services.research_data_quality_analytics_service import ResearchDataQualityAnalyticsService
from app.services.school_performance_analytics_service import SchoolPerformanceAnalyticsService
from app.services.teaching_research_balance_analytics_service import TeachingResearchBalanceAnalyticsService

security = HTTPBearer(auto_error=False)


def require_analytics_role(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """FastAPI Dependency for token authentication & role validation."""
    return verify_analytics_role(credentials)


def get_analytics_service(
    db: Session = Depends(get_db),
) -> ResearchAnalyticsService:
    """FastAPI Dependency for ResearchAnalyticsService."""
    return ResearchAnalyticsService(db)


def get_faculty_research_analytics_service(
    db: Session = Depends(get_db),
) -> FacultyResearchAnalyticsService:
    """FastAPI Dependency for faculty email based research analytics."""
    return FacultyResearchAnalyticsService(db)


def get_books_analytics_service(
    db: Session = Depends(get_db),
) -> BooksAnalyticsService:
    """FastAPI Dependency for BooksAnalyticsService."""
    return BooksAnalyticsService(db)


def get_journals_analytics_service(
    db: Session = Depends(get_db),
) -> JournalsAnalyticsService:
    """FastAPI Dependency for JournalsAnalyticsService."""
    return JournalsAnalyticsService(db)


def get_patents_analytics_service(
    db: Session = Depends(get_db),
) -> PatentsAnalyticsService:
    """FastAPI Dependency for PatentsAnalyticsService."""
    return PatentsAnalyticsService(db)


def get_projects_funding_analytics_service(
    db: Session = Depends(get_db),
) -> ProjectsFundingAnalyticsService:
    """FastAPI Dependency for ProjectsFundingAnalyticsService."""
    return ProjectsFundingAnalyticsService(db)


def get_conferences_awards_analytics_service(
    db: Session = Depends(get_db),
) -> ConferencesAwardsAnalyticsService:
    """FastAPI Dependency for ConferencesAwardsAnalyticsService."""
    return ConferencesAwardsAnalyticsService(db)


def get_innovation_pipeline_analytics_service(
    db: Session = Depends(get_db),
) -> InnovationPipelineAnalyticsService:
    """FastAPI Dependency for InnovationPipelineAnalyticsService."""
    return InnovationPipelineAnalyticsService(db)


def get_faculty_performance_analytics_service(
    db: Session = Depends(get_db),
) -> FacultyPerformanceAnalyticsService:
    """FastAPI Dependency for FacultyPerformanceAnalyticsService."""
    return FacultyPerformanceAnalyticsService(db)


def get_department_performance_analytics_service(
    db: Session = Depends(get_db),
) -> DepartmentPerformanceAnalyticsService:
    """FastAPI Dependency for DepartmentPerformanceAnalyticsService."""
    return DepartmentPerformanceAnalyticsService(db)


def get_school_performance_analytics_service(
    db: Session = Depends(get_db),
) -> SchoolPerformanceAnalyticsService:
    """FastAPI Dependency for SchoolPerformanceAnalyticsService."""
    return SchoolPerformanceAnalyticsService(db)


def get_teaching_research_balance_analytics_service(
    db: Session = Depends(get_db),
) -> TeachingResearchBalanceAnalyticsService:
    """FastAPI Dependency for TeachingResearchBalanceAnalyticsService."""
    return TeachingResearchBalanceAnalyticsService(db)


def get_appraisal_completion_analytics_service(
    db: Session = Depends(get_db),
) -> AppraisalCompletionAnalyticsService:
    """FastAPI Dependency for AppraisalCompletionAnalyticsService."""
    return AppraisalCompletionAnalyticsService(db)


def get_research_data_quality_analytics_service(
    db: Session = Depends(get_db),
) -> ResearchDataQualityAnalyticsService:
    """FastAPI Dependency for ResearchDataQualityAnalyticsService."""
    return ResearchDataQualityAnalyticsService(db)











