from fastapi import APIRouter, Query
from app.scoring.checklists import ChecklistEngine

router = APIRouter(prefix="/api/v2/checklists", tags=["Checklists"])

@router.get("/")
def checklist(symbol: str = Query(...)):
    engine = ChecklistEngine()
    return engine.generate(symbol)
