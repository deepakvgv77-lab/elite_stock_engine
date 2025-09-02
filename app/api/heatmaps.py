from fastapi import APIRouter, Query
from app.scoring.heatmaps import HeatmapEngine

router = APIRouter(prefix="/api/v2/heatmaps", tags=["Heatmaps"])

@router.get("/")
def heatmap(sector: str = Query(...)):
    engine = HeatmapEngine()
    return engine.generate(sector)
