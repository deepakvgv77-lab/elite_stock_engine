from typing import Dict

class ModelRegistry:
    def register(self, name: str, version: str, metadata: Dict):
        # Implement persist model registry info
        pass

    def rollback(self, name: str, version: str):
        # Implement model rollback logic
        pass
