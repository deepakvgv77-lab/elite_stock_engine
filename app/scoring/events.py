from typing import List, Dict

class EventDrivenEngine:
    def run(self, payload: List[Dict]) -> List[Dict]:
        results = []
        for event in payload:
            score = self._score_event(event)
            results.append({"event_id": event.get("id"), "fund_score": score})
        return results

    def _score_event(self, event: Dict) -> float:
        # Placeholder for fund/tech event scoring
        return 65.0
