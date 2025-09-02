from typing import List, Dict
from app.core.database import db_manager

class IPOScoringEngine:
    def score_upcoming(self) -> List[Dict]:
        ipos = db_manager.execute_query("SELECT * FROM upcoming_ipos")
        results = []
        for ipo in ipos:
            score = (ipo.get('eps', 0) * 25)
            if ipo.get('pe_ratio', 0) < ipo.get('sector_pe', 100):
                score += 15
            score = min(score, 100)
            results.append({**ipo, "score": score})
        return results
