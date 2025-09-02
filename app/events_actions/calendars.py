from typing import List, Dict
from app.core.database import db_manager

class CalendarService:
    def get_dividends(self, days: int = 7) -> List[Dict]:
        return db_manager.execute_query(
            "SELECT symbol, amount, record_date, ex_date FROM corporate_actions "
            "WHERE type='DIVIDEND' AND ex_date BETWEEN CURRENT_DATE AND DATE('now','+? days')", [days]
        )

    def get_agm(self, days: int = 7) -> List[Dict]:
        return db_manager.execute_query(
            "SELECT symbol, date AS agm_date FROM corporate_actions "
            "WHERE type IN ('AGM','EGM') AND date BETWEEN CURRENT_DATE AND DATE('now','+? days')", [days]
        )
