class GuardrailPolicies:
    def validate(self, trade: dict) -> bool:
        # Example trade validation
        spread_ok = trade.get("spread", 0) < 0.5
        liquidity_ok = trade.get("liquidity", 0) > 1000
        return spread_ok and liquidity_ok
