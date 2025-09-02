from datetime import datetime
from app.core.database import db_manager
from loguru import logger

async def monitor_system_health():
    logger.info("Performing system health check")
    try:
        result = db_manager.execute_query("SELECT 1")
        if result:
            # Update health table or monitoring tool here
            logger.info("Database connectivity: UP")
        else:
            logger.warning("Database connectivity: DOWN")
    except Exception as e:
        logger.error(f"Health check error: {e}")
