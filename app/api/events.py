from fastapi import APIRouter, Body
from typing import List, Dict
from app.scoring.events import EventDrivenEngine

router = APIRouter(prefix="/api/v2/events", tags=["Events"])

@router.post("/score")
def event_scores(payload: List[Dict] = Body(...)):
    engine = EventDrivenEngine()
    return engine.run(payload)
