from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from asyncio import get_event_loop
from datetime import datetime
from loguru import logger
from app.tasks.data_refresh import refresh_market_data, refresh_gold_data
from app.tasks.health_monitor import monitor_system_health
from app.core.config import settings

scheduler = AsyncIOScheduler()

def start_scheduler():
    logger.info("Starting Elite Stock Engine Scheduler")

    # Market data refresh every 15 seconds
    scheduler.add_job(refresh_market_data, IntervalTrigger(seconds=settings.AUTO_REFRESH_INTERVAL), id="market_refresh")

    # Gold price refresh every 30 minutes
    scheduler.add_job(refresh_gold_data, IntervalTrigger(minutes=30), id="gold_refresh")

    # Health monitor every 1 minute
    scheduler.add_job(monitor_system_health, IntervalTrigger(minutes=1), id="health_monitor")

    scheduler.start()

def shutdown_scheduler():
    logger.info("Shutting down Elite Stock Engine Scheduler")
    scheduler.shutdown(wait=False)

if __name__ == "__main__":
    start_scheduler()
    loop = get_event_loop()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        shutdown_scheduler()
