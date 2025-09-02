from fastapi import APIRouter, Body
from typing import List, Dict
from app.governance.model_registry import ModelRegistry
from app.governance.drift_monitor import DriftMonitor
from app.governance.rulepacks import RulePackManager

router = APIRouter(prefix="/api/v5/governance", tags=["Governance"])
mr = ModelRegistry()
dm = DriftMonitor()
rp = RulePackManager()

@router.post("/register")
async def register_model(name: str = Body(...), version: str = Body(...), metadata: Dict = Body(...)):
    mr.register(name, version, metadata)
    return {"status": "registered"}

@router.post("/rollback")
async def rollback_model(name: str = Body(...), version: str = Body(...)):
    mr.rollback(name, version)
    return {"status": "rolled_back"}

@router.post("/drift")
async def detect_drift(predictions: List[float] = Body(...), truths: List[float] = Body(...)):
    return {"drift_score": dm.detect(predictions, truths)}

@router.post("/reload_rulepack")
async def reload_rulepack(pack: str = Body(...)):
    rp.hot_reload(pack)
    return {"status": "reloaded"}
