from typing import List, Dict

class BTSTEngine:
    def run(self, symbols: List[str]) -> List[Dict]:
        results = []
        for symbol in symbols:
            btst_score = self._calculate_btst(symbol)
            results.append({"symbol": symbol, "btst_score": btst_score})
        return results

    def _calculate_btst(self, symbol: str) -> float:
        # Placeholder BTST logic and guardrails
        return 75.0  # example fixed score
