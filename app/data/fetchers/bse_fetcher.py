import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from app.data.fetchers.base_fetcher import BaseFetcher
from app.core.config import settings, BSE_ENDPOINTS
from app.core.models import Quote, Exchange, DataSource

class BSEFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.base_url = settings.BSE_BASE_URL
        self.client = httpx.AsyncClient(
            headers={"User-Agent": settings.USER_AGENT}, timeout=30
        )

    async def test_connectivity(self) -> Dict[str, Any]:
        """Implements abstract connectivity test by hitting a simple endpoint."""
        url = f"{self.base_url}{BSE_ENDPOINTS['market_status']}"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            ok = resp.status_code == 200
            logger.info(f"BSE connectivity test success: {ok}")
            return {"bse_connectivity": ok}
        except Exception as e:
            logger.error(f"BSE connectivity test failed: {e}")
            return {"bse_connectivity": False}

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def safe_fetch(self, fetch_func, *args, **kwargs):
        return await super().safe_fetch(fetch_func, *args, **kwargs)

    async def fetch_stock_universe(self) -> List[Dict[str, Any]]:
        """
        Fetch full BSE universe from HTML master page.
        Returns list of dicts with stock metadata.
        """
        url = f"{self.base_url}{BSE_ENDPOINTS['sensex_data']}"
        try:
            resp = await self.safe_fetch(self.client.get, url)
            resp.raise_for_status()
            html = resp.text
            # TODO: Implement actual HTML parsing of BSE master list page.
            universe = []
            logger.info("Fetched BSE universe (parsing not implemented, placeholder empty list)")
            return universe
        except Exception as e:
            logger.error(f"BSE universe fetch error: {e}")
            return []

    async def fetch_equity_quote(self, symbol: str) -> Optional[Quote]:
        """
        Fetch live quote for individual stock symbol.
        Parsing of HTML response needed to extract actual values.
        """
        url = f"{self.base_url}{BSE_ENDPOINTS['equity_info']}{symbol}"
        try:
            resp = await self.safe_fetch(self.client.get, url)
            resp.raise_for_status()
            html = resp.text
            # TODO: Parse HTML to extract quote data.
            quote_data = {
                "symbol": symbol,
                "exchange": Exchange.BSE,
                "price": 0.0,
                "change_amount": 0.0,
                "change_percent": 0.0,
                "volume": None,
                "value": None,
                "high": None,
                "low": None,
                "open": None,
                "close": None,
                "data_source": DataSource.BSE_HTML,
                "timestamp": datetime.now(),
            }
            return Quote(**quote_data)
        except Exception as e:
            logger.error(f"BSE quote fetch error for {symbol}: {e}")
            return None

    async def fetch_multiple_quotes(self, symbols: List[str]) -> List[Quote]:
        """
        Fetch multiple quotes concurrently with limited concurrency.
        """
        if not symbols:
            return []
        semaphore = asyncio.Semaphore(5)
        async def fetch(symbol: str) -> Optional[Quote]:
            async with semaphore:
                await asyncio.sleep(0.1)
                return await self.fetch_equity_quote(symbol)
        results = await asyncio.gather(*(fetch(s) for s in symbols), return_exceptions=True)
        quotes = []
        for result in results:
            if isinstance(result, Quote):
                quotes.append(result)
            else:
                logger.error(f"Error fetching BSE quote: {result}")
        logger.info(f"Fetched {len(quotes)} of {len(symbols)} BSE quotes")
        return quotes
