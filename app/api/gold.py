from fastapi import APIRouter, Query, HTTPException
from typing import List
from datetime import datetime, timedelta, date
from app.core.database import db_manager
from app.core.models import GoldRateResponse

router = APIRouter(prefix="/api/v1/gold", tags=["Gold"])

@router.get("/current", response_model=GoldRateResponse)
def get_current_gold_rate(city: str = "Coimbatore", purity: str = "22K"):
    query = """
        SELECT * FROM gold_rates 
        WHERE city = ? AND purity = ? 
        ORDER BY date DESC LIMIT 1
    """
    result = db_manager.execute_query(query, [city, purity])
    if not result:
        raise HTTPException(status_code=404, detail="No gold rate found for specified parameters")
    rate = result[0]

    # Compute trend direction
    trend = None
    if rate.get('change_amount', 0) > 0:
        trend = "UP"
    elif rate.get('change_amount', 0) < 0:
        trend = "DOWN"
    else:
        trend = "STABLE"

    return GoldRateResponse(
        date=rate["date"],
        city=rate["city"],
        purity=rate["purity"],
        rate_per_gram=rate["rate_per_gram"],
        rate_per_10g=rate["rate_per_10g"],
        change_amount=rate.get("change_amount"),
        change_percent=rate.get("change_percent"),
        trend_direction=trend,
        data_source=rate.get("data_source"),
    )

@router.get("/history", response_model=List[GoldRateResponse])
def get_gold_history(city: str = "Coimbatore", purity: str = "22K", days: int = Query(30, le=365)):
    query = """
        SELECT * FROM gold_rates
        WHERE city = ? AND purity = ? AND date >= DATE('now', ? || ' days')
        ORDER BY date DESC
    """
    results = db_manager.execute_query(query, [city, purity, f"-{days}"])
    if not results:
        raise HTTPException(status_code=404, detail="No gold rate history found")

    def map_row(row):
        trend = "UP" if (row.get('change_amount') or 0) > 0 else "DOWN" if (row.get('change_amount') or 0) < 0 else "STABLE"
        return GoldRateResponse(
            date=row['date'],
            city=row['city'],
            purity=row['purity'],
            rate_per_gram=row['rate_per_gram'],
            rate_per_10g=row['rate_per_10g'],
            change_amount=row.get('change_amount'),
            change_percent=row.get('change_percent'),
            trend_direction=trend,
            data_source=row.get('data_source')
        )

    return [map_row(r) for r in results]

@router.post("/refresh")
async def refresh_gold_data():
    # Placeholder for triggering async refresh tasks or scraping
    return {"status": "Triggered gold data refresh"}
