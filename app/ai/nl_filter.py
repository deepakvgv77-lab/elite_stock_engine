from typing import Dict

class NLFilter:
    def parse(self, query: str) -> Dict:
        tokens = query.lower().split()
        filters = {}
        if "buy" in tokens:
            filters["action"] = "BUY"
        if "sector" in tokens:
            idx = tokens.index("sector")
            if idx + 1 < len(tokens):
                filters["sector"] = tokens[idx + 1].title()
        return filters
