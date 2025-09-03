import httpx
from typing import Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger

from tenacity import retry, stop_after_attempt, wait_exponential

from app.data.fetchers.base_fetcher import BaseFetcher
from app.core.config import settings, GOLD_ENDPOINTS
from app.core.models import GoldRate, DataSource

class GoldFetcher(BaseFetcher):
    def __init__(self):
        super().__init__()
        self.base_url = settings.GOLD_BASE_URL
        self.client = httpx.AsyncClient(timeout=30)

    async def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity by fetching the city rates page."""
        url = f"{self.base_url}{GOLD_ENDPOINTS['city_page'].format(city='Coimbatore')}"
        try:
            resp = await self.client.get(url)
            ok = resp.status_code == 200
            return {"gold_connectivity": ok}
        except Exception as e:
            logger.error(f"Gold connectivity test failed: {e}")
            return {"gold_connectivity": False}

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def safe_fetch(self, fetch_func, *args, **kwargs):
        return await super().safe_fetch(fetch_func, *args, **kwargs)

    async def fetch_gold_rates(self) -> List[Dict[str, Any]]:
        """
        Fetch gold rates for Coimbatore 22K: current + last 10 days.
        Returns list of dicts matching GoldRate schema.
        """
        city = "Coimbatore"
        purity = "22K"
        url = f"{self.base_url}{GOLD_ENDPOINTS['city_page'].format(city=city)}"
        try:
            resp = await self.safe_fetch(self.client.get, url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # Example: parse the table rows for date and rate columns
            rows = soup.select("table.rate-table tbody tr")
            rates: List[Dict[str, Any]] = []
            for row in rows[:11]:  # header + 10 days
                cols = [td.get_text(strip=True) for td in row.select("td")]
                date_str, rate_str = cols[0], cols[1]
                rate_per_gram = float(rate_str.replace(",", ""))
                rate_per_10g = rate_per_gram * 10
                change_amount = None
                change_percent = None
                previous_rate = None
                rates.append({
                    "date": datetime.strptime(date_str, "%d-%m-%Y").date(),
                    "city": city,
                    "purity": purity,
                    "rate_per_gram": rate_per_gram,
                    "rate_per_10g": rate_per_10g,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                    "previous_rate": previous_rate,
                    "data_source": DataSource.GOLD_WEBSITE,
                })
            logger.info(f"Fetched {len(rates)} gold rates for {city}")
            return rates
        except Exception as e:
            logger.error(f"Gold rates fetch failed: {e}")
            return []
