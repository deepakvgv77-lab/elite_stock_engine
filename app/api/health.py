from fastapi import APIRouter
from datetime import datetime
from app.core.models import HealthResponse, HealthStatus, SystemHealthCheck
from app.core.database import db_manager

router = APIRouter(prefix="/api/v1/health", tags=["Health"])

@router.get("/", response_model=HealthResponse)
def get_health():
    # Check database connectivity
    try:
        db_manager.execute_query("SELECT 1")
        db_status = HealthStatus.UP
    except Exception:
        db_status = HealthStatus.DOWN

    # Collect component health checks (only DB for now)
    components = [
        SystemHealthCheck(component="Database", status=db_status, checked_at=datetime.utcnow())
    ]

    # Data freshness example
    freshness = {"quotes": 60}  # seconds; can derive dynamically

    return HealthResponse(
        status=HealthStatus.UP if db_status == HealthStatus.UP else HealthStatus.DEGRADED,
        timestamp=datetime.utcnow(),
        components=components,
        data_freshness=freshness,
        uptime_seconds=None
    )
