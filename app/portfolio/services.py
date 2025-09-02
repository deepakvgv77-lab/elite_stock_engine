from datetime import datetime
from typing import List
from .crud import list_holdings
from .models import PortfolioHealth
from app.core.database import db_manager

def calculate_xirr(dates, amounts) -> float:
    # Simplified placeholder XIRR calculation
    return 12.5

def diversification_score(holdings) -> float:
    # Simplified diversification scoring
    return 75.0

def risk_exposure(holdings) -> float:
    # Simplified risk scoring
    return 30.0

def compute_health(user_id: str) -> PortfolioHealth:
    holdings = list_holdings(user_id)
    total_value = 0.0
    dates, amts = [], []

    for h in holdings:
        latest_quote = db_manager.execute_query(
            "SELECT price FROM quotes WHERE symbol=? ORDER BY timestamp DESC LIMIT 1", [h['symbol']]
        )
        price = latest_quote[0]['price'] if latest_quote else 0
        current_val = price * h['quantity']
        total_value += current_val
        dates.append(h['added_at'])
        amts.append(-h['avg_price'] * h['quantity'])
    dates.append(datetime.utcnow().date())
    amts.append(total_value)

    xirr = calculate_xirr(dates, amts)

    return PortfolioHealth(
        total_value=total_value,
        xirr=xirr,
        health_score=diversification_score(holdings),
        diversification_score=diversification_score(holdings),
        risk_exposure=risk_exposure(holdings)
    )
