from typing import Dict
import numpy as np

class MonteCarlo:
    def simulate(self, model: Dict, runs: int = 1000) -> Dict:
        returns = np.random.normal(model.get("mean", 0), model.get("std", 1), runs)
        return {"mean_return": np.mean(returns), "std_return": np.std(returns)}
