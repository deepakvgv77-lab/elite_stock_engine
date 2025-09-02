from typing import Dict
from app.core.database import db_manager

class CatalystCardsService:
    def generate_card(self, symbol: str, event_id: int) -> Dict:
        event = db_manager.execute_query(
            "SELECT * FROM corporate_actions WHERE id = ?", [event_id]
        )[0]
        fund = event.get('impact_fund_score', 0)
        tech = event.get('impact_tech_score', 0)
        prob = min(1.0, (fund + tech) / 200)
        rec  = "BUY" if prob > 0.6 else "HOLD" if prob > 0.4 else "AVOID"
        return {
            "symbol": symbol,
            "event": event['type'],
            "scoreFund": fund,
            "scoreTech": tech,
            "impactProb": prob,
            "recommendation": rec
        }
