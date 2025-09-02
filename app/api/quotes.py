from fastapi import APIRouter, Query, HTTPException
from typing import List
from datetime import datetime, timedelta
from app.core.database import db_manager
from app.core.models import QuoteResponse, Exchange

router = APIRouter(prefix="/api/v1/quotes", tags=["Quotes"])

@router.get("/", response_model=List[QuoteResponse])
def get_quotes(symbols: List[str] = Query(..., description="List of stock symbols"), exchange: Exchange = Exchange.NSE):
    if not symbols:
        raise HTTPException(status_code=400, detail="Symbols list cannot be empty")

    placeholders = ",".join(["?"] * len(symbols))
    query = f"""
        SELECT q.symbol, s.name, q.exchange, q.price, q.change_amount, q.change_percent,
               q.volume, q.high, q.low, q.timestamp
        FROM quotes q
        JOIN stocks s ON q.symbol = s.symbol
        WHERE q.symbol IN ({placeholders})
          AND q.exchange = ?
        ORDER BY q.timestamp DESC
    """
    params = [*symbols, exchange.value]
    rows = db_manager.execute_query(query, params)

    if not rows:
        raise HTTPException(status_code=404, detail="No quotes found for provided symbols")

    count = 0
    results = []
    now = datetime.utcnow()
    for row in rows:
        staleness = (now - row['timestamp']).total_seconds() / 60 if row['timestamp'] else None
        results.append(QuoteResponse(
            symbol=row['symbol'],
            name=row.get('name'),
            exchange=row['exchange'],
            price=row['price'],
            change_amount=row.get('change_amount'),
            change_percent=row.get('change_percent'),
            volume=row.get('volume'),
            high=row.get('high'),
            low=row.get('low'),
            timestamp=row['timestamp'],
            staleness_minutes=int(staleness) if staleness else None
        ))
        count += 1

    return results
