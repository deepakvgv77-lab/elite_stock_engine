from fastapi import APIRouter, Query
from typing import List
from app.scoring.btst import BTSTEngine

router = APIRouter(prefix="/api/v2/btst", tags=["BTST"])

@router.get("/score")
def btst_scores(symbols: List[str] = Query(...)):
    engine = BTSTEngine()
    return engine.run(symbols)
