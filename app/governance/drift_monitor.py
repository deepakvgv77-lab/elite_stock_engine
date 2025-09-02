from typing import List

class DriftMonitor:
    def detect(self, predictions: List[float], truths: List[float]) -> float:
        diffs = [abs(p - t) for p, t in zip(predictions, truths)]
        return sum(diffs) / len(diffs) if diffs else 0.0
