from typing import Dict, List

class AdaptiveWeighting:
    def tune(self, scores: List[Dict]) -> Dict:
        if not scores:
            return {}
        keys = scores[0].get("subscores", {}).keys()
        evenly_distributed = 1 / max(len(keys), 1)
        return {k: evenly_distributed for k in keys}
