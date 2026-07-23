from app.api.deps import require_analytics_role
from app.api.v1.router import api_v1_router as router

__all__ = ["router", "require_analytics_role"]
