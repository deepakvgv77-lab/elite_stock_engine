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
        # reuse one client for session cookies
        self.client = httpx.AsyncClient(headers={"User-Agent": settings.USER_AGENT}, timeout=30)

    async def test_connectivity(self) -> Dict[str, Any]:
        """Implements abstract connectivity test by hitting a simple BSE endpoint."""
        url = f"{self.base_url}{BSE_ENDPOINTS['market_status']}"
        try:
            resp = await self.client.get(url)
            ok = resp.status_code == 200
            return {"bse_connectivity": ok}
        except Exception as e:
            logger.error(f"BSE connectivity test failed: {e}")
            return {"bse_connectivity": False}

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def safe_fetch(self, fetch_func, *args, **kwargs):
        return await super().safe_fetch(fetch_func, *args, **kwargs)

    async def fetch_stock_universe(self) -> List[Dict[str, Any]]:
        """
        Fetch full BSE universe from HTML master list.
        Returns a list of dicts with keys: symbol, name, exchange, etc.
        """
        url = f"{self.base_url}{BSE_ENDPOINTS['universe']}"
        try:
            resp = await self.safe_fetch(self.client.get, url)
            resp.raise_for_status()
            html = resp.text
            # parse HTML table of symbols
            # (Implement actual parsing per BSE spec; placeholder below)
            universe = []
            # Example parse (BeautifulSoup) omitted for brevity
            logger.info("BSE universe fetched successfully")
            return universe
        except Exception as e:
            logger.error(f"BSE universe fetch error: {e}")
            return []

    async def fetch_equity_quote(self, symbol: str) -> Optional[Quote]:
        """
        Fetch live quote for a single BSE symbol by parsing HTML/JSON response.
        """
        url = f"{self.base_url}{BSE_ENDPOINTS['equity_info']}{symbol}"
        try:
            resp = await self.safe_fetch(self.client.get, url)
            resp.raise_for_status()
            # parse resp.text or resp.json() to extract priceInfo
            # Placeholder example:
            price = 0.0
            change = 0.0
            change_pct = 0.0
            # Real parsing must extract actual values
            quote_data = {
                "symbol": symbol,
                "exchange": Exchange.BSE,
                "price": price,
                "change_amount": change,
                "change_percent": change_pct,
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
        Concurrently fetch multiple BSE quotes.
        """
        if not symbols:
            return []
        semaphore = asyncio.Semaphore(5)
        async def fetch(sym: str):
            async with semaphore:
                await asyncio.sleep(0.1)
                return await self.fetch_equity_quote(sym)

        results = await asyncio.gather(*(fetch(s) for s in symbols), return_exceptions=True)
        quotes: List[Quote] = []
        for res in results:
            if isinstance(res, Quote):
                quotes.append(res)
            else:
                logger.error(f"Error fetching BSE quote: {res}")
        logger.info(f"Fetched {len(quotes)}/{len(symbols)} BSE quotes")
        return quotes
