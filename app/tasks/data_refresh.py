from loguru import logger
from app.data.fetchers.nse_fetcher import NSEFetcher
from app.data.fetchers.bse_fetcher import BSEFetcher
from app.data.fetchers.gold_fetcher import GoldFetcher

async def refresh_market_data():
    logger.info("Starting market data refresh")
    nse_fetcher = NSEFetcher()
    bse_fetcher = BSEFetcher()
    try:
        await nse_fetcher.initialize_session()
        # Example: refresh NSE market status or universe here

        # TODO: Implement fetching of critical market data and update database
        logger.info("NSE market data refreshed")
    except Exception as e:
        logger.error(f"Market data refresh failed: {e}")

    try:
        # TODO: Implement BSE data refresh logic
        logger.info("BSE market data refreshed")
    except Exception as e:
        logger.error(f"BSE data refresh failed: {e}")

async def refresh_gold_data():
    gold_fetcher = GoldFetcher()
    try:
        await gold_fetcher.fetch_current_rate()
        logger.info("Gold data refreshed successfully")
    except Exception as e:
        logger.error(f"Gold data refresh failed: {e}")
