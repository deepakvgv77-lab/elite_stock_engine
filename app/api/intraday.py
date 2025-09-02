from fastapi import APIRouter, Query
from typing import List
from app.scoring.intraday import IntradayPacks

router = APIRouter(prefix="/api/v2/intraday", tags=["Intraday"])

@router.get("/score")
def intraday_scores(symbols: List[str] = Query(...)):
    engine = IntradayPacks()
    return engine.run(symbols)
