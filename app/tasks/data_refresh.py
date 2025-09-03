from __future__ import annotations

import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.database import db_manager
from app.data.fetchers.nse_fetcher import NSEFetcher
from app.data.fetchers.bse_fetcher import BSEFetcher
from app.data.fetchers.gold_fetcher import GoldFetcher


# ---------------------------
# Utilities
# ---------------------------

def _gen_pk() -> int:
    """Generate a reasonably unique integer PK suitable for DuckDB INTEGER PRIMARY KEY."""
    # Uses time in microseconds for a compact but unique-ish number.
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


def _ensure_stock_row(symbol: str, name: Optional[str], exchange: str) -> None:
    """
    Ensure a minimal row exists in stocks to satisfy FK for quotes.
    Uses ON CONFLICT DO NOTHING on (symbol) primary key.
    """
    try:
        sql = """
            INSERT INTO stocks (symbol, name, exchange)
            VALUES (?, ?, ?)
            ON CONFLICT (symbol) DO NOTHING
        """
        params = [symbol, name or symbol, exchange]
        db_manager.execute_insert(sql, params)
    except Exception as e:
        # Don't block quotes insert if stocks upsert fails; log and continue.
        logger.warning(f"stocks upsert skipped for {symbol} ({exchange}): {e}")


# ---------------------------
# Public Tasks (exported)
# ---------------------------

async def refresh_market_data() -> Dict[str, Any]:
    """
    Refresh market data for NSE and BSE:
      - Fetch quotes from both exchanges
      - Upsert minimal stocks rows to satisfy FK
      - Insert quotes into 'quotes' table
    Returns summary counts.
    """
    logger.info("Starting market data refresh")

    nse_fetcher = NSEFetcher()
    bse_fetcher = BSEFetcher()

    total_inserted = {"NSE": 0, "BSE": 0}
    total_errors = {"NSE": 0, "BSE": 0}

    # ---------- NSE ----------
    try:
        if hasattr(nse_fetcher, "initialize_session"):
            try:
                await nse_fetcher.initialize_session()
                logger.info("NSE session initialized successfully")
            except Exception as se:
                logger.warning(f"NSE session init skipped/failed: {se}")

        # Prefer multi-symbol method if available
        if hasattr(nse_fetcher, "fetch_all_quotes"):
            nse_quotes = await nse_fetcher.fetch_all_quotes()
        elif hasattr(nse_fetcher, "fetch_quotes"):
            # If your fetcher needs symbols, you could pull top symbols from DB here
            nse_quotes = await nse_fetcher.fetch_quotes()
        else:
            nse_quotes = []

        insert_query = """
            INSERT INTO quotes (
                id, symbol, exchange, price, change_amount, change_percent, volume, value,
                high, low, open, close, bid, ask, delivery_qty, delivery_percent,
                timestamp, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for q in nse_quotes or []:
            try:
                symbol = _get_attr(q, "symbol")
                name = _get_attr(q, "name", default=symbol)
                exchange = _get_attr(q, "exchange", default="NSE")
                if hasattr(exchange, "value"):
                    exchange = exchange.value

                # Ensure stocks row (FK safety)
                _ensure_stock_row(symbol, name, exchange)

                params = [
                    _gen_pk(),
                    symbol,
                    exchange or "NSE",
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
                total_inserted["NSE"] += 1
            except Exception as e:
                total_errors["NSE"] += 1
                logger.error(f"NSE quote insert failed for {_get_attr(q, 'symbol')}: {e}")

        logger.info(f"NSE market data refreshed | inserted={total_inserted['NSE']}, errors={total_errors['NSE']}")
    except Exception as e:
        logger.error(f"NSE market data refresh failed: {e}")

    # ---------- BSE ----------
    try:
        # Prefer multi-symbol method if available
        if hasattr(bse_fetcher, "fetch_all_quotes"):
            bse_quotes = await bse_fetcher.fetch_all_quotes()
        elif hasattr(bse_fetcher, "fetch_quotes"):
            bse_quotes = await bse_fetcher.fetch_quotes()
        else:
            bse_quotes = []

        insert_query = """
            INSERT INTO quotes (
                id, symbol, exchange, price, change_amount, change_percent, volume, value,
                high, low, open, close, bid, ask, delivery_qty, delivery_percent,
                timestamp, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for q in bse_quotes or []:
            try:
                symbol = _get_attr(q, "symbol")
                name = _get_attr(q, "name", default=symbol)
                exchange = _get_attr(q, "exchange", default="BSE")
                if hasattr(exchange, "value"):
                    exchange = exchange.value

                # Ensure stocks row (FK safety)
                _ensure_stock_row(symbol, name, exchange)

                params = [
                    _gen_pk(),
                    symbol,
                    exchange or "BSE",
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
                total_inserted["BSE"] += 1
            except Exception as e:
                total_errors["BSE"] += 1
                logger.error(f"BSE quote insert failed for {_get_attr(q, 'symbol')}: {e}")

        logger.info(f"BSE market data refreshed | inserted={total_inserted['BSE']}, errors={total_errors['BSE']}")
    except Exception as e:
        logger.error(f"BSE market data refresh failed: {e}")

    summary = {
        "NSE": total_inserted["NSE"],
        "BSE": total_inserted["BSE"],
        "errors": {"NSE": total_errors["NSE"], "BSE": total_errors["BSE"]},
    }
    logger.info(f"Market data refresh summary: {summary}")
    return summary


async def refresh_gold_data(city: str = "Coimbatore", purity: str = "22K") -> Dict[str, Any]:
    """
    Refresh current gold rate and upsert into gold_rates (unique by date, city, purity).
    """
    logger.info(f"Refreshing gold rates | city={city}, purity={purity}")

    gold_fetcher = GoldFetcher()
    try:
        gr = await gold_fetcher.fetch_current_rate(city=city, purity=purity)
    except Exception as e:
        logger.error(f"Gold data fetch failed: {e}")
        return {"updated": False, "error": str(e)}

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
        logger.info(f"Gold rates upserted | date={g_date} city={g_city} purity={g_purity}")
        return {
            "updated": True,
            "date": str(g_date),
            "city": g_city,
            "purity": g_purity,
            "rate_per_gram": rate_per_gram,
            "rate_per_10g": rate_per_10g,
        }
    except Exception as e:
        logger.error(f"Failed to upsert gold rates: {e}")
        return {"updated": False, "error": str(e)}


# Explicit exports for scheduler imports
__all__ = ["refresh_market_data", "refresh_gold_data"]
