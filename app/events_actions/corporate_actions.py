from typing import List, Dict
from app.core.database import db_manager

class CorporateActionsService:
    def fetch_actions(self) -> List[Dict]:
        return db_manager.execute_query(
            "SELECT * FROM corporate_actions WHERE ex_date >= CURRENT_DATE"
        )

    def simulate_impact(self, symbol: str, action_id: int) -> Dict:
        action = db_manager.execute_query(
            "SELECT * FROM corporate_actions WHERE id = ?", [action_id]
        )[0]
        factor = 1.0
        if action['type'] == 'BONUS':
            factor = (action['ratio_numerator'] + action['ratio_denominator']) / action['ratio_denominator']
        return {"symbol": symbol, "action_id": action_id, "adjustment_factor": factor}
