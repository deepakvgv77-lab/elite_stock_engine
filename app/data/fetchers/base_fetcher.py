from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.utils.circuit_breaker import CircuitBreaker

class BaseFetcher(ABC):
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
        self.last_fetch_time: Optional[datetime] = None
        self.fetch_count = 0
        self.error_count = 0

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def safe_fetch(self, fetch_func, *args, **kwargs):
        try:
            result = await self.circuit_breaker.call(fetch_func, *args, **kwargs)
            self.fetch_count += 1
            self.last_fetch_time = datetime.now()
            return result
        except Exception as e:
            self.error_count += 1
            logger.error(f"Fetch failed after retries: {e}")
            raise

    @abstractmethod
    async def test_connectivity(self) -> Dict[str, Any]:
        pass

    def get_stats(self) -> Dict[str, Any]:
        return {
            "fetch_count": self.fetch_count,
            "error_count": self.error_count,
            "success_rate": (self.fetch_count - self.error_count) / max(self.fetch_count, 1) * 100,
            "last_fetch_time": self.last_fetch_time,
            "circuit_breaker_state": self.circuit_breaker.state,
        }
