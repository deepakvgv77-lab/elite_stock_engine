from loguru import logger
from app.data.fetchers.nse_fetcher import NSEFetcher
from app.data.fetchers.bse_fetcher import BSEFetcher
from app.core.database import db_manager

async def refresh_market_data():
    logger.info("Starting market data refresh")
    nse_fetcher = NSEFetcher()
    bse_fetcher = BSEFetcher()

    try:
        await nse_fetcher.initialize_session()
        nse_quotes = await nse_fetcher.fetch_quotes()

        insert_query = """
            INSERT INTO quotes (
                id, symbol, exchange, price, change_amount, change_percent,
                volume, value, high, low, open, close, bid, ask,
                delivery_qty, delivery_percent, timestamp, data_source
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

        inserted_nse = 0
        for quote in nse_quotes:
            try:
                db_manager.execute_insert(insert_query, [
                    quote["id"], quote["symbol"], "NSE", quote["price"], quote.get("change_amount"),
                    quote.get("change_percent"), quote.get("volume"), quote.get("value"),
                    quote.get("high"), quote.get("low"), quote.get("open"), quote.get("close"),
                    quote.get("bid"), quote.get("ask"), quote.get("delivery_qty"),
                    quote.get("delivery_percent"), quote.get("timestamp"), "API"
                ])
                inserted_nse += 1
            except Exception as e:
                logger.warning(f"Failed to insert NSE quote for {quote['symbol']}: {e}")

        logger.info(f"NSE market data refreshed with {inserted_nse} quotes")
    except Exception as e:
        logger.error(f"NSE market data refresh failed: {e}")

    try:
        bse_quotes = await bse_fetcher.fetch_quotes()

        inserted_bse = 0
        for quote in bse_quotes:
            try:
                db_manager.execute_insert(insert_query, [
                    quote["id"], quote["symbol"], "BSE", quote["price"], quote.get("change_amount"),
                    quote.get("change_percent"), quote.get("volume"), quote.get("value"),
                    quote.get("high"), quote.get("low"), quote.get("open"), quote.get("close"),
                    quote.get("bid"), quote.get("ask"), quote.get("delivery_qty"),
                    quote.get("delivery_percent"), quote.get("timestamp"), "API"
                ])
                inserted_bse += 1
            except Exception as e:
                logger.warning(f"Failed to insert BSE quote for {quote['symbol']}: {e}")

        logger.info(f"BSE market data refreshed with {inserted_bse} quotes")
    except Exception as e:
        logger.error(f"BSE market data refresh failed: {e}")
