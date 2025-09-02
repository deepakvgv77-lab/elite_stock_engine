from typing import List, Dict
import numpy as np

class Backtester:
    def run(self, signals: List[Dict], slippage: float = 0.001) -> Dict:
        returns = [s.get("return", 0) - slippage for s in signals]
        total_return = sum(returns)
        sharpe_ratio = total_return / (np.std(returns) if len(returns) > 1 else 1)
        return {"total_return": total_return, "sharpe": sharpe_ratio}
