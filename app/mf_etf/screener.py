from typing import Dict, List
from app.core.database import db_manager

class MFScreener:
    def run(self, filters: Dict) -> List[Dict]:
        sql = "SELECT * FROM mutual_funds WHERE nav > ? AND expense_ratio < ?"
        return db_manager.execute_query(sql, [filters.get('min_nav', 0), filters.get('max_er', 0.05)])

class ETFScreener:
    def run(self, filters: Dict) -> List[Dict]:
        sql = "SELECT * FROM etfs WHERE tracking_error < ? AND liquidity > ?"
        return db_manager.execute_query(sql, [filters.get('max_te', 0.02), filters.get('min_liq', 10000)])
