import httpx
from typing import Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger

from tenacity import retry, stop_after_attempt, wait_exponential

from app.data.fetchers.base_fetcher import BaseFetcher
from app.core.config import settings, GOLD_SOURCES
from app.core.models import GoldRate, DataSource

class GoldFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.city = settings.GOLD_CITY
        self.purity = settings.GOLD_PURITY
        self.urls = [
            GOLD_SOURCES["primary"],
            GOLD_SOURCES["secondary"],
            GOLD_SOURCES["tertiary"],
        ]
        self.client = httpx.AsyncClient(timeout=30)

    async def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity by fetching the primary gold rate page."""
        try:
            resp = await self.client.get(self.urls[0])
            return {"gold_connectivity": resp.status_code == 200}
        except Exception as e:
            logger.error(f"Gold connectivity test failed: {e}")
            return {"gold_connectivity": False}

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def safe_fetch(self, fetch_func, *args, **kwargs):
        return await super().safe_fetch(fetch_func, *args, **kwargs)

    async def fetch_gold_rates(self) -> List[Dict[str, Any]]:
        """
        Fetch gold rates for the city (Coimbatore) at 22K purity
        using the prioritized list of data sources. Returns a list
        of dicts compatible with GoldRate schema.
        """
        for url in self.urls:
            try:
                resp = await self.safe_fetch(self.client.get, url)
                resp.raise_for_status()
                html = resp.text
                rates = self._parse_rates_from_html(url, html)
                if rates:
                    logger.info(f"Gold rates fetched successfully from {url}")
                    return rates
                else:
                    logger.warning(f"No rates parsed from {url}")
            except Exception as e:
                logger.warning(f"Failed to fetch gold rates from {url}: {e}")
        logger.error("All gold data sources failed")
        return []

    def _parse_rates_from_html(self, url: str, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        rates = []
        # Parsing implementation for 'goodreturns.in' (primary source)
        if "goodreturns.in" in url:
            table = soup.find("table", {"class": "gold-rate-table"})
            if not table:
                logger.warning("Gold rates table not found in goodreturns.in page")
                return []
            rows = table.find_all("tr")[1:]  # skip header
            for row in rows[:10]:  # last 10 days
                cols = row.find_all("td")
                if len(cols) < 2:
                    continue
                date_str = cols[0].get_text(strip=True)
                rate_str = cols[1].get_text(strip=True).replace(",", "")
                try:
                    date_obj = datetime.strptime(date_str, "%d %b %Y").date()
                    rate_per_gram = float(rate_str)
                    rate_per_10g = rate_per_gram * 10
                    rates.append({
                        "date": date_obj,
                        "city": self.city,
                        "purity": self.purity,
                        "rate_per_gram": rate_per_gram,
                        "rate_per_10g": rate_per_10g,
                        "change_amount": None,
                        "change_percent": None,
                        "previous_rate": None,
                        "data_source": DataSource.GOLD_WEBSITE,
                    })
                except Exception as e:
                    logger.warning(f"Error parsing row in goodreturns.in: {e}")
            return rates

        # TODO: Add parsing logic for secondary and tertiary sources similarly

        logger.warning(f"No parser implemented for source: {url}")
        return []
