import httpx
import asyncio
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from loguru import logger
from app.data.fetchers.base_fetcher import BaseFetcher
from app.core.config import settings, NSE_ENDPOINTS
from app.core.models import Quote, Exchange, DataSource

class NSEFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.base_url = settings.NSE_BASE_URL
        self.session_cookies = {}
        self.headers = {
            'User-Agent': settings.USER_AGENT,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/',
        }

    async def initialize_session(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.base_url, headers=self.headers, follow_redirects=True)
                if response.status_code == 200:
                    self.session_cookies = dict(response.cookies)
                    logger.info("NSE session initialized successfully")
                    return True
                else:
                    logger.error(f"Failed to initialize NSE session: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"NSE session initialization error: {e}")
            return False

    async def fetch_market_status(self) -> Dict[str, Any]:
        endpoint = NSE_ENDPOINTS["market_status"]
        url = f"{self.base_url}{endpoint}"

        try:
            if not self.session_cookies:
                await self.initialize_session()

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=self.headers, cookies=self.session_cookies)
                if response.status_code == 200:
                    data = response.json()
                    logger.info("NSE market status fetched successfully")
                    return data
                else:
                    logger.error(f"NSE market status fetch failed: {response.status_code}")
                    return {}
        except Exception as e:
            logger.error(f"NSE market status fetch error: {e}")
            return {}

    async def fetch_equity_quote(self, symbol: str) -> Optional[Quote]:
        endpoint = f"{NSE_ENDPOINTS['equity_info']}{symbol}"
        url = f"{self.base_url}{endpoint}"
        try:
            if not self.session_cookies:
                await self.initialize_session()

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=self.headers, cookies=self.session_cookies)
                if response.status_code == 200:
                    data = response.json()
                    quote_data = self._parse_equity_quote(data, symbol)
                    if quote_data:
                        return Quote(**quote_data)
                else:
                    logger.warning(f"NSE quote fetch failed for {symbol}: {response.status_code}")
        except Exception as e:
            logger.error(f"NSE quote fetch error for {symbol}: {e}")
        return None

    def _parse_equity_quote(self, data: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        try:
            info = data.get('info', {})
            price_info = data.get('priceInfo', {})
            quote_data = {
                'symbol': symbol,
                'exchange': Exchange.NSE,
                'price': float(price_info.get('lastPrice', 0)),
                'change_amount': float(price_info.get('change', 0)),
                'change_percent': float(price_info.get('pChange', 0)),
                'volume': int(price_info.get('totalTradedVolume', 0)),
                'value': int(price_info.get('totalTradedValue', 0)),
                'high': float(price_info.get('intraDayHighLow', {}).get('max', 0)),
                'low': float(price_info.get('intraDayHighLow', {}).get('min', 0)),
                'open': float(price_info.get('open', 0)),
                'close': float(price_info.get('previousClose', 0)),
                'data_source': DataSource.NSE_API,
                'timestamp': datetime.now()
            }
            if quote_data['price'] > 0:
                return quote_data
            else:
                logger.warning(f"Invalid price data for {symbol}")
                return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing NSE quote for {symbol}: {e}")
            return None

    async def fetch_multiple_quotes(self, symbols: List[str]) -> List[Quote]:
        if not symbols:
            return []

        semaphore = asyncio.Semaphore(5)

        async def fetch(symbol: str) -> Optional[Quote]:
            async with semaphore:
                await asyncio.sleep(0.1)
                return await self.fetch_equity_quote(symbol)

        tasks = [fetch(sym) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        quotes = []
        for res in results:
            if isinstance(res, Quote):
                quotes.append(res)
            else:
                logger.error(f"Error fetching quote: {res}")
        logger.info(f"Successfully fetched {len(quotes)} quotes out of {len(symbols)} requested")
        return quotes
