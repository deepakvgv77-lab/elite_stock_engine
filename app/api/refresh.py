from __future__ import annotations

import asyncio
import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.core.database import db_manager
from app.data.fetchers.nse_fetcher import NSEFetcher
from app.data.fetchers.bse_fetcher import BSEFetcher
from app.data.fetchers.gold_fetcher import GoldFetcher

router = APIRouter(prefix="/refresh", tags=["Data Refresh"])


# ---------------------------
# Utilities
# ---------------------------

def _gen_pk() -> int:
    """Generate a reasonably unique integer PK suitable for DuckDB INTEGER PRIMARY KEY."""
    # Uses time in nanoseconds; in very high concurrency you can add a small per-process counter.
    return time.time_ns() // 1000


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Return obj.name if present; else obj['name'] if dict; else default."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


# ---------------------------
# Service
# ---------------------------

class RefreshService:
    """Manual refresh service for live data sources"""

    def __init__(self):
        self.nse_fetcher = NSEFetcher()
        self.bse_fetcher = BSEFetcher()
        self.gold_fetcher = GoldFetcher()

    # -------- NSE QUOTES --------
    async def refresh_nse_quotes(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Refresh NSE quotes for specified symbols or for top symbols if not provided."""
        logger.info("Starting NSE quotes refresh")

        # If no symbols specified, get top symbols from database
        if not symbols:
            popular_symbols_query = """
                SELECT DISTINCT symbol FROM stocks
                WHERE exchange = 'NSE'
                ORDER BY market_cap DESC NULLS LAST
                LIMIT 50
            """
            rows = db_manager.execute_query(popular_symbols_query)
            symbols = [row["symbol"] for row in rows] if rows else ["RELIANCE", "TCS", "INFY"]
            logger.debug(f"NSE symbols selected for refresh: {symbols[:10]}{'...' if len(symbols) > 10 else ''}")

        # Initialize session if fetcher supports it
        try:
            if hasattr(self.nse_fetcher, "initialize_session"):
                await self.nse_fetcher.initialize_session()
        except Exception as e:
            logger.warning(f"NSE session initialization failed/unsupported: {e}")

        # Fetch quotes
        try:
            if hasattr(self.nse_fetcher, "fetch_multiple_quotes"):
                quotes = await self.nse_fetcher.fetch_multiple_quotes(symbols)
            elif hasattr(self.nse_fetcher, "fetch_quotes"):
                quotes = await self.nse_fetcher.fetch_quotes(symbols)
            else:
                raise RuntimeError("NSEFetcher lacks a quotes fetching method")
        except Exception as e:
            logger.error(f"Failed to fetch NSE quotes: {e}")
            raise HTTPException(status_code=502, detail="Failed to fetch NSE quotes")

        insert_query = """
            INSERT INTO quotes (
                id, symbol, exchange, price, change_amount, change_percent, volume, value,
                high, low, open, close, bid, ask, delivery_qty, delivery_percent,
                timestamp, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted = 0
        errors = 0
        for q in quotes or []:
            try:
                # Be liberal about the data shape (dict or object)
                symbol = _get_attr(q, "symbol")
                exchange_value = _get_attr(q, "exchange")
                if hasattr(exchange_value, "value"):
                    exchange_value = exchange_value.value
                if not exchange_value:
                    exchange_value = "NSE"

                params = [
                    _gen_pk(),
                    symbol,
                    exchange_value,
                    _as_float(_get_attr(q, "price")),
                    _as_float(_get_attr(q, "change_amount")),
                    _as_float(_get_attr(q, "change_percent")),
                    _get_attr(q, "volume"),
                    _get_attr(q, "value"),
                    _as_float(_get_attr(q, "high")),
                    _as_float(_get_attr(q, "low")),
                    _as_float(_get_attr(q, "open")),
                    _as_float(_get_attr(q, "close")),
                    _as_float(_get_attr(q, "bid")),
                    _as_float(_get_attr(q, "ask")),
                    _get_attr(q, "delivery_qty"),
                    _as_float(_get_attr(q, "delivery_percent")),
                    _get_attr(q, "timestamp") or datetime.utcnow(),
                    _get_attr(_get_attr(q, "data_source"), "value", default="API") or "API",
                ]
                db_manager.execute_insert(insert_query, params)
                inserted += 1
            except Exception as e:
                errors += 1
                logger.error(f"NSE quote insert failed for {_get_attr(q, 'symbol')}: {e}")

        logger.info(f"NSE quotes refresh completed | inserted={inserted}, errors={errors}")
        return {"exchange": "NSE", "symbols_count": len(symbols), "inserted": inserted, "errors": errors}

    # -------- BSE QUOTES --------
    async def refresh_bse_quotes(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Refresh BSE quotes for specified symbols or for top symbols if not provided."""
        logger.info("Starting BSE quotes refresh")

        if not symbols:
            popular_symbols_query = """
                SELECT DISTINCT symbol FROM stocks
                WHERE exchange = 'BSE'
                ORDER BY market_cap DESC NULLS LAST
                LIMIT 50
            """
            rows = db_manager.execute_query(popular_symbols_query)
            symbols = [row["symbol"] for row in rows] if rows else ["RELIANCE", "TCS", "INFY"]
            logger.debug(f"BSE symbols selected for refresh: {symbols[:10]}{'...' if len(symbols) > 10 else ''}")

        # Fetch BSE quotes
        try:
            if hasattr(self.bse_fetcher, "fetch_multiple_quotes"):
                quotes = await self.bse_fetcher.fetch_multiple_quotes(symbols)
            elif hasattr(self.bse_fetcher, "fetch_quotes"):
                quotes = await self.bse_fetcher.fetch_quotes(symbols)
            else:
                raise RuntimeError("BSEFetcher lacks a quotes fetching method")
        except Exception as e:
            logger.error(f"Failed to fetch BSE quotes: {e}")
            raise HTTPException(status_code=502, detail="Failed to fetch BSE quotes")

        insert_query = """
            INSERT INTO quotes (
                id, symbol, exchange, price, change_amount, change_percent, volume, value,
                high, low, open, close, bid, ask, delivery_qty, delivery_percent,
                timestamp, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted = 0
        errors = 0
        for q in quotes or []:
            try:
                symbol = _get_attr(q, "symbol")
                exchange_value = _get_attr(q, "exchange")
                if hasattr(exchange_value, "value"):
                    exchange_value = exchange_value.value
                if not exchange_value:
                    exchange_value = "BSE"

                params = [
                    _gen_pk(),
                    symbol,
                    exchange_value,
                    _as_float(_get_attr(q, "price")),
                    _as_float(_get_attr(q, "change_amount")),
                    _as_float(_get_attr(q, "change_percent")),
                    _get_attr(q, "volume"),
                    _get_attr(q, "value"),
                    _as_float(_get_attr(q, "high")),
                    _as_float(_get_attr(q, "low")),
                    _as_float(_get_attr(q, "open")),
                    _as_float(_get_attr(q, "close")),
                    _as_float(_get_attr(q, "bid")),
                    _as_float(_get_attr(q, "ask")),
                    _get_attr(q, "delivery_qty"),
                    _as_float(_get_attr(q, "delivery_percent")),
                    _get_attr(q, "timestamp") or datetime.utcnow(),
                    _get_attr(_get_attr(q, "data_source"), "value", default="API") or "API",
                ]
                db_manager.execute_insert(insert_query, params)
                inserted += 1
            except Exception as e:
                errors += 1
                logger.error(f"BSE quote insert failed for {_get_attr(q, 'symbol')}: {e}")

        logger.info(f"BSE quotes refresh completed | inserted={inserted}, errors={errors}")
        return {"exchange": "BSE", "symbols_count": len(symbols), "inserted": inserted, "errors": errors}

    # -------- GOLD --------
    async def refresh_gold(self, city: str = "Coimbatore", purity: str = "22K") -> Dict[str, Any]:
        """Refresh current gold rates and upsert into gold_rates."""
        logger.info(f"Refreshing gold rates | city={city}, purity={purity}")
        try:
            # Expected to return an object or dict with at least: date, rate_per_gram, rate_per_10g
            gr = await self.gold_fetcher.fetch_current_rate(city=city, purity=purity)
        except Exception as e:
            logger.error(f"Failed to fetch gold rates: {e}")
            raise HTTPException(status_code=502, detail="Failed to fetch gold rates")

        # Normalize fields
        g_date: date = _get_attr(gr, "date") or date.today()
        g_city = _get_attr(gr, "city", city) or city
        g_purity = _get_attr(gr, "purity", purity) or purity
        rate_per_gram = _as_float(_get_attr(gr, "rate_per_gram"))
        rate_per_10g = _as_float(_get_attr(gr, "rate_per_10g"))
        change_amount = _as_float(_get_attr(gr, "change_amount"))
        change_percent = _as_float(_get_attr(gr, "change_percent"))
        previous_rate = _as_float(_get_attr(gr, "previous_rate"))
        data_source = _get_attr(_get_attr(gr, "data_source"), "value", default="API") or "API"

        # Upsert using ON CONFLICT (DuckDB supports upsert on unique constraints)
        # Unique constraint is (date, city, purity)
        upsert_sql = """
            INSERT INTO gold_rates (
                id, date, city, purity, rate_per_gram, rate_per_10g,
                change_amount, change_percent, previous_rate, data_source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (date, city, purity) DO UPDATE SET
                rate_per_gram=excluded.rate_per_gram,
                rate_per_10g=excluded.rate_per_10g,
                change_amount=excluded.change_amount,
                change_percent=excluded.change_percent,
                previous_rate=excluded.previous_rate,
                data_source=excluded.data_source
        """
        try:
            params = [
                _gen_pk(),
                g_date,
                g_city,
                g_purity,
                rate_per_gram,
                rate_per_10g,
                change_amount,
                change_percent,
                previous_rate,
                data_source,
            ]
            db_manager.execute_insert(upsert_sql, params)
        except Exception as e:
            logger.error(f"Failed to upsert gold rates: {e}")
            raise HTTPException(status_code=500, detail="Failed to upsert gold rates")

        logger.info(f"Gold rates updated | date={g_date} city={g_city} purity={g_purity}")
        return {
            "date": str(g_date),
            "city": g_city,
            "purity": g_purity,
            "rate_per_gram": rate_per_gram,
            "rate_per_10g": rate_per_10g,
            "change_amount": change_amount,
            "change_percent": change_percent,
        }

    # -------- MARKET STATUS --------
    async def refresh_market_status(self) -> Dict[str, Any]:
        """Refresh NSE market status and log into system_health."""
        logger.info("Refreshing NSE market status")
        try:
            status = await self.nse_fetcher.fetch_market_status()
        except Exception as e:
            logger.error(f"Failed to fetch NSE market status: {e}")
            raise HTTPException(status_code=502, detail="Failed to fetch market status")

        is_up: bool = bool(_get_attr(status, "is_open", default=bool(status)))
        response_time_ms = _get_attr(status, "response_time_ms")
        status_value = "UP" if is_up else "DOWN"

        # Insert a health record (id required by your schema)
        health_sql = """
            INSERT INTO system_health (id, component, status, response_time_ms, error_message, checked_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        try:
            db_manager.execute_insert(
                health_sql,
                [
                    _gen_pk(),
                    "NSE Market",
                    status_value,
                    int(response_time_ms) if response_time_ms is not None else None,
                    None,
                ],
            )
        except Exception as e:
            logger.error(f"Failed to record system health: {e}")
            # Don't fail the request if logging health fails
        logger.info(f"NSE market status updated: {status_value}")
        return {"market_status": status_value, "response_time_ms": response_time_ms}


service = RefreshService()


# ---------------------------
# Routes
# ---------------------------

@router.post("/nse-quotes")
async def post_refresh_nse_quotes(
    symbols: Optional[List[str]] = Query(None, description="List of NSE stock symbols (optional)")
) -> Dict[str, Any]:
    """
    Refresh NSE quotes for specified symbols. If not provided, top ~50 by market cap will be used.
    """
    return await service.refresh_nse_quotes(symbols)


@router.post("/bse-quotes")
async def post_refresh_bse_quotes(
    symbols: Optional[List[str]] = Query(None, description="List of BSE stock symbols (optional)")
) -> Dict[str, Any]:
    """
    Refresh BSE quotes for specified symbols. If not provided, top ~50 by market cap will be used.
    """
    return await service.refresh_bse_quotes(symbols)


@router.post("/gold")
async def post_refresh_gold(
    city: str = Query("Coimbatore", description="City to refresh gold for"),
    purity: str = Query("22K", description="Gold purity (e.g., 22K, 24K)")
) -> Dict[str, Any]:
    """Refresh and upsert current gold rates."""
    return await service.refresh_gold(city=city, purity=purity)


@router.post("/market-status")
async def post_refresh_market_status() -> Dict[str, Any]:
    """Refresh and record NSE market status."""
    return await service.refresh_market_status()


@router.post("/all")
async def post_refresh_all(
    nse_symbols: Optional[List[str]] = Query(None, description="NSE symbols (optional)"),
    bse_symbols: Optional[List[str]] = Query(None, description="BSE symbols (optional)"),
    gold_city: str = Query("Coimbatore", description="City for gold"),
    gold_purity: str = Query("22K", description="Purity for gold")
) -> Dict[str, Any]:
    """
    Run all refreshers concurrently: NSE quotes, BSE quotes, gold, and market status.
    """
    started_at = datetime.utcnow().isoformat()
    logger.info("Starting combined refresh: NSE, BSE, Gold, Market Status")

    results = {"started_at": started_at}

    tasks = [
        service.refresh_nse_quotes(nse_symbols),
        service.refresh_bse_quotes(bse_symbols),
        service.refresh_gold(city=gold_city, purity=gold_purity),
        service.refresh_market_status(),
    ]
    try:
        nse_res, bse_res, gold_res, status_res = await asyncio.gather(*tasks, return_exceptions=True)
        # Normalize exceptions into readable dicts for the response
        results["nse"] = nse_res if not isinstance(nse_res, Exception) else {"error": str(nse_res)}
        results["bse"] = bse_res if not isinstance(bse_res, Exception) else {"error": str(bse_res)}
        results["gold"] = gold_res if not isinstance(gold_res, Exception) else {"error": str(gold_res)}
        results["market_status"] = status_res if not isinstance(status_res, Exception) else {"error": str(status_res)}
    except Exception as e:
        logger.error(f"Combined refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Combined refresh failed")

    results["finished_at"] = datetime.utcnow().isoformat()
    logger.info("Combined refresh finished")
