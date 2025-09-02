from fastapi import APIRouter, Body, Query
from typing import List, Dict
from app.backtest.backtester import Backtester
from app.backtest.pit_loader import PITLoader
from app.backtest.walk_forward import WalkForward
from app.backtest.monte_carlo import MonteCarlo

router = APIRouter(prefix="/api/v5/backtest", tags=["Backtesting"])
bt = Backtester()
pit = PITLoader()
wf = WalkForward()
mc = MonteCarlo()

@router.post("/run")
async def run_backtest(signals: List[Dict] = Body(...)):
    return bt.run(signals)

@router.get("/pit")
async def load_pit(as_of: str = Query(...)):
    from datetime import date
    return pit.load(date.fromisoformat(as_of))

@router.post("/walkforward")
async def walk_forward(strategy: Dict = Body(...)):
    return wf.optimize(strategy)

@router.post("/montecarlo")
async def monte_carlo(model: Dict = Body(...), runs: int = Body(1000)):
    return mc.simulate(model, runs)
