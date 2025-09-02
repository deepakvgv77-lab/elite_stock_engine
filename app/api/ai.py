from fastapi import APIRouter, Body, Query
from typing import Dict, List
from app.ai.nl_filter import NLFilter
from app.ai.sentiment import SentimentEngine
from app.ai.explainability import ExplainEngine
from app.ai.scenario import ScenarioNarrative
from app.ai.adaptive_weighting import AdaptiveWeighting

router = APIRouter(prefix="/api/v5/ai", tags=["AI"])
nlf = NLFilter()
sentiment = SentimentEngine()
explain = ExplainEngine()
scenario = ScenarioNarrative()
adaptive = AdaptiveWeighting()

@router.post("/nl2filters")
async def nl2filters(query: str = Body(...)):
    return nlf.parse(query)

@router.get("/sentiment")
async def sentiment_score(symbol: str = Query(...)):
    return sentiment.analyze(symbol)

@router.post("/explain")
async def explain_model(model: Dict = Body(...), data: Dict = Body(...)):
    import pandas as pd, joblib
    clf = joblib.load(model["path"])
    df = pd.DataFrame(data)
    return explain.explain(clf, df)

@router.get("/scenario")
async def generate_scenario(symbol: str = Query(...), regime: str = Query(...)):
    return {"narrative": scenario.generate(symbol, regime)}

@router.post("/adaptive")
async def adaptive_weights(scores: List[Dict] = Body(...)):
    return adaptive.tune(scores)
