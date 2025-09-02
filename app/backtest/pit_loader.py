from datetime import date
from typing import Dict

class PITLoader:
    def load(self, as_of: date) -> Dict:
        return {"date": as_of.isoformat(), "universe_size": 7500}
