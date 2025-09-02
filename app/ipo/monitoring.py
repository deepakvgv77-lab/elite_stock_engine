from typing import Dict
from app.core.database import db_manager

class IPOMonitor:
    def pre_list(self, symbol: str) -> Dict:
        sub = db_manager.execute_query(
            "SELECT subscription, gmp FROM ipo_subscriptions WHERE symbol=?", [symbol]
        )
        return {"symbol": symbol, **(sub[0] if sub else {})}

    def post_list(self, symbol: str) -> Dict:
        price = db_manager.execute_query(
            "SELECT listing_price FROM listing_prices WHERE symbol=?", [symbol]
        )
        return {"symbol": symbol, "listing_price": price[0]['listing_price'] if price else None}
