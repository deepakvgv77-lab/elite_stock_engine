from fastapi import APIRouter, Query
from app.scoring.diagnostics import DiagnosticsEngine

router = APIRouter(prefix="/api/v2/diagnostics", tags=["Diagnostics"])

@router.get("/")
def diagnostics(symbol: str = Query(...)):
    engine = DiagnosticsEngine()
    return engine.run(symbol)
