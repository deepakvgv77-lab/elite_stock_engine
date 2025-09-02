from fastapi import APIRouter, Query
from typing import List
from app.scoring.ultra_elite import UltraEliteScreener

router = APIRouter(prefix="/api/v2/ultra", tags=["Ultra"])

@router.get("/score")
def ultra_scores(symbols: List[str] = Query(...)):
    screener = UltraEliteScreener()
    return screener.run(symbols)
