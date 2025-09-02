from typing import Dict

class IPOEntryStrategy:
    def plan(self, symbol: str, fair_value: float, listing_price: float) -> Dict:
        action = "BUY" if listing_price < fair_value else "WAIT"
        return {
            "symbol": symbol,
            "action": action,
            "target_price": fair_value,
            "stop_loss": fair_value * 0.9,
        }
