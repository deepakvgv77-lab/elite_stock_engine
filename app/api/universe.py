from fastapi import APIRouter
from datetime import datetime
from app.core.database import db_manager
from app.core.models import UniverseStatsResponse

router = APIRouter(prefix="/api/v1/universe", tags=["Universe"])

@router.get("/stats", response_model=UniverseStatsResponse)
def get_universe_stats():
    # Total stocks
    total_stocks_query = "SELECT COUNT(*) AS count FROM stocks"
    total_stocks = db_manager.execute_query(total_stocks_query)[0]['count']

    # NSE and BSE counts
    nse_count_query = "SELECT COUNT(*) AS count FROM stocks WHERE exchange = 'NSE'"
    nse_count = db_manager.execute_query(nse_count_query)[0]['count']
    bse_count_query = "SELECT COUNT(*) AS count FROM stocks WHERE exchange = 'BSE'"
    bse_count = db_manager.execute_query(bse_count_query)[0]['count']

    # Last updated timestamp from quotes table
    last_updated_query = "SELECT MAX(timestamp) AS last_updated FROM quotes"
    last_updated_row = db_manager.execute_query(last_updated_query)
    last_updated = last_updated_row[0]['last_updated'] if last_updated_row else None

    freshness = {}
    if last_updated:
        freshness['quotes'] = (datetime.utcnow() - last_updated).total_seconds()

    return UniverseStatsResponse(
        total_stocks=total_stocks,
        nse_stocks=nse_count,
        bse_stocks=bse_count,
        last_updated=last_updated,
        data_freshness=freshness
    )
