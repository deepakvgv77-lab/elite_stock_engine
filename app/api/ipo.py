from fastapi import APIRouter, Query
from typing import List, Dict
from app.ipo.scoring import IPOScoringEngine
from app.ipo.monitoring import IPOMonitor
from app.ipo.strategy import IPOEntryStrategy

router = APIRouter(prefix="/api/v4/ipo", tags=["IPO"])
engine = IPOScoringEngine()
monitor = IPOMonitor()
strate = IPOEntryStrategy()

@router.get("/upcoming", response_model=List[Dict])
def upcoming():
    return engine.score_upcoming()

@router.get("/prelist", response_model=Dict)
def prelist(symbol: str = Query(...)):
    return monitor.pre_list(symbol)

@router.get("/postlist", response_model=Dict)
def postlist(symbol: str = Query(...)):
    return monitor.post_list(symbol)

@router.get("/strategy", response_model=Dict)
def strategy(symbol: str = Query(...), fair_value: float = Query(...), listing_price: float = Query(...)):
    return strate.plan(symbol, fair_value, listing_price)
