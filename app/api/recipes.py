from fastapi import APIRouter, Body, Query
from typing import Dict, List
from app.scoring.recipes import RecipeEngine

router = APIRouter(prefix="/api/v2/recipes", tags=["Recipes"])
engine = RecipeEngine()

@router.post("/save")
def save_recipe(payload: Dict = Body(...)):
    name = payload.get("name")
    filters = payload.get("filters")
    success = engine.save(name, filters)
    return {"saved": success}

@router.get("/run")
def run_recipe(name: str = Query(...)):
    return engine.run(name)
