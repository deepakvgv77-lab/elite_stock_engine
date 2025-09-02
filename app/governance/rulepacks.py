from typing import Dict

class RulePackManager:
    def load(self, pack: str) -> Dict:
        return {"rules": []}

    def hot_reload(self, pack: str):
        pass
