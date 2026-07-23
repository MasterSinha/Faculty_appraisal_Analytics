from typing import Generator
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_analytics_role
from app.database import get_db
from app.services.research_analytics_service import ResearchAnalyticsService

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
