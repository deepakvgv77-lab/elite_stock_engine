from typing import Dict, List

class RecipeEngine:
    def __init__(self):
        self.saved_recipes = {}

    def save(self, name: str, filters: Dict) -> bool:
        self.saved_recipes[name] = filters
        return True

    def run(self, name: str) -> List[Dict]:
        filters = self.saved_recipes.get(name)
        if not filters:
            return []
        # Simulate applying filters to database query
        return [{"symbol": "RECIPE1", "score": 80}]
