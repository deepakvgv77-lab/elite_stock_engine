from typing import Dict, Any
import shap
import pandas as pd

class ExplainEngine:
    def explain(self, model: Any, X: pd.DataFrame) -> Dict:
        explainer = shap.Explainer(model.predict, X)
        shap_values = explainer(X)
        return {
            "feature_names": X.columns.tolist(),
            "shap_values": shap_values.values.tolist()
        }
