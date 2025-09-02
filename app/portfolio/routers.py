from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .models import Holding, HoldingCreate, PortfolioHealth
from .crud import create_holding, list_holdings, delete_holding
from .services import compute_health
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v3/portfolio", tags=["Portfolio"])

@router.post("/holdings", response_model=int)
def add_holding(h: HoldingCreate, user=Depends(get_current_user)):
    return create_holding(user.id, h)

@router.get("/holdings", response_model=List[Holding])
def get_holdings(user=Depends(get_current_user)):
    return list_holdings(user.id)

@router.delete("/holdings/{hid}")
def remove_holding(hid: int, user=Depends(get_current_user)):
    delete_holding(user.id, hid)
    return {"status": "deleted"}

@router.get("/health", response_model=PortfolioHealth)
def health(user=Depends(get_current_user)):
    return compute_health(user.id)
