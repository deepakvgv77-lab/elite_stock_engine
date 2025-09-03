from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from loguru import logger

from app.core.models import RefreshResponse
from app.core.database import db_manager
from app.data.fetchers.nse_fetcher import NSEFetcher

router = APIRouter(prefix="/refresh", tags=["Data Refresh"])


class RefreshService:
    """Manual refresh service for live data sources"""

    def __init__(self):
        self.nse_fetcher = NSEFetcher()

    async def refresh_nse_quotes(self, symbols: List[str] = None) -> Dict[str, int]:
        """Refresh NSE quotes for specified symbols or top symbols"""
        try:
            logger.info("Starting NSE quotes refresh")

            # If no symbols specified, get top symbols from database
            if not symbols:
                popular_symbols_query = """
                SELECT DISTINCT symbol FROM stocks 
                WHERE exchange = 'NSE' 
                ORDER BY market_cap DESC NULLS LAST 
                LIMIT 50
                """
                result = db_manager.execute_query(popular_symbols_query)
                symbols = [row["symbol"] for row in result] if result else ["RELIANCE", "TCS", "INFY"]

            quotes = await self.nse_fetcher.fetch_multiple_quotes(symbols)
            quotes_updated = 0

            for quote in quotes:
                try:
                    quote_query = """
                    INSERT INTO quotes (
                        symbol, exchange, price, change_amount, change_percent, volume, value,
                        high, low, open, close, timestamp, data_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = {
                        "symbol": quote.symbol,
                        "exchange": quote.exchange.value,
                        "price": float(quote.price),
                        "change_amount": float(quote.change_amount) if quote.change_amount is not None else None,
                        "change_percent": float(quote.change_percent) if quote.change_percent is not None else None,
                        "volume": quote.volume,
                        "value": quote.value,
                        "high": float(quote.high) if quote.high is not None else None,
                        "low": float(quote.low) if quote.low is not None else None,
                        "open": float(quote.open) if quote.open is not None else None,
                        "close": float(quote.close) if quote.close is not None else None,
                        "timestamp": quote.timestamp,
                        "data_source": quote.data_source.value,
                    }
                    db_manager.execute_insert(quote_query, params)
                    quotes_updated += 1
                except Exception as e:
                    logger.error(f"Failed to insert quote for {quote.symbol}: {e}")

            logger.info(f"NSE quotes refresh completed: {quotes_updated} quotes updated")
            return {"quotes": quotes_updated}

        except Exception as e:
            logger.error(f"NSE quotes refresh failed: {e}")
            raise

    async def refresh_market_status(self) -> Dict[str, Any]:
        """Refresh NSE market status"""
        try:
            logger.info("Refreshing NSE market status")
            market_status = await self.nse_fetcher.fetch_market_status()

            status_value = "UP" if market_status else "DOWN"
            health_query = """
            INSERT INTO system_health (component, status, response_time_ms, checked_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """
            db_manager.execute_insert(
                health_query,
                {
                    "component": "NSE_Market",
                    "status": status_value,
                    "response_time_ms": None,
                },
            )

            return {"market_status": status_value}

        except Exception as e:
            logger.error(f"Market status refresh failed: {e}")
            raise

    async def get_fetcher_stats(self) -> Dict[str, Any]:
        """Get statistics from fetchers"""
        return {
            "nse": self.nse_fetcher.get_stats(),
        }


refresh_service = RefreshService()


@router.post("/", response_model=RefreshResponse)
async def manual_refresh(
    sources: Optional[List[str]] = None,
    symbols: Optional[List[str]] = None,
) -> RefreshResponse:
    """
    Manual refresh endpoint for live data sources.

    Args:
      sources: List of sources to refresh ["nse", "market_status"].
      symbols: List of symbols to refresh quotes for.

    Returns:
      RefreshResponse with status and metrics.
    """
    start_time = datetime.now()

    try:
        if sources is None:
            sources = ["nse"]

        valid_sources = {"nse", "market_status"}
        invalid = set(sources) - valid_sources
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sources: {list(invalid)}. Valid: {list(valid_sources)}",
            )

        sources_refreshed: List[str] = []
        records_updated: Dict[str, Any] = {}
        errors: List[str] = []

        if "nse" in sources:
            try:
                nse_res = await refresh_service.refresh_nse_quotes(symbols)
                sources_refreshed.append("NSE")
                records_updated.update(nse_res)
            except Exception as e:
                errors.append(f"NSE refresh failed: {e}")

        if "market_status" in sources:
            try:
                st_res = await refresh_service.refresh_market_status()
                sources_refreshed.append("MARKET_STATUS")
                records_updated.update(st_res)
            except Exception as e:
                errors.append(f"Market status failed: {e}")

        duration = (datetime.now() - start_time).total_seconds()
        success = len(errors) == 0

        return RefreshResponse(
            triggered_at=start_time,
            sources_refreshed=sources_refreshed,
            records_updated=records_updated,
            validation_status={"basic": "PASSED" if success else "FAILED"},
            duration_seconds=duration,
            success=success,
            errors=errors or None,
        )

    except HTTPException:
        raise
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Manual refresh failed: {e}")
        return RefreshResponse(
            triggered_at=start_time,
            sources_refreshed=[],
            records_updated={},
            validation_status={"error": str(e)},
            duration_seconds=duration,
            success=False,
            errors=[str(e)],
        )


@router.get("/status")
async def get_refresh_status():
    """Get current refresh status and data freshness."""
    try:
        latest_quotes = db_manager.execute_query("SELECT MAX(timestamp) as latest_quote FROM quotes")
        latest_stocks = db_manager.execute_query("SELECT MAX(updated_at) as latest_stock FROM stocks")
        fetcher_stats = await refresh_service.get_fetcher_stats()

        return {
            "status": "ready",
            "data_freshness": {
                "quotes": latest_quotes[0]["latest_quote"] if latest_quotes else None,
                "stocks": latest_stocks[0]["latest_stock"] if latest_stocks else None,
            },
            "fetcher_stats": fetcher_stats,
            "timestamp": datetime.now(),
        }

    except Exception as e:
        logger.error(f"Failed to get refresh status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get refresh status")


@router.post("/watchlist")
async def refresh_watchlist_data(symbols: List[str]):
    """
    Refresh specific watchlist symbols only.
    """
    start_time = datetime.now()

    try:
        logger.info(f"Refreshing watchlist symbols: {symbols}")
        result = await refresh_service.refresh_nse_quotes(symbols)
        duration = (datetime.now() - start_time).total_seconds()

        return {
            "triggered_at": start_time,
            "symbols_requested": len(symbols),
            "quotes_updated": result.get("quotes", 0),
            "duration_seconds": duration,
            "success": True,
            "errors": None,
        }

    except Exception as e:
        logger.error(f"Watchlist refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Watchlist refresh failed: {e}")


@router.get("/test-connectivity")
async def test_connectivity():
    """Test connectivity to all data sources."""
    try:
        nse_test = await refresh_service.nse_fetcher.test_connectivity()
        return {"nse": nse_test, "timestamp": datetime.now()}
    except Exception as e:
        logger.error(f"Connectivity test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connectivity test failed: {e}")
