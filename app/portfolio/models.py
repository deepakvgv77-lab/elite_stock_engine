from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class HoldingCreate(BaseModel):
    symbol: str = Field(..., max_length=20)
    quantity: float
    avg_price: float

class Holding(HoldingCreate):
    id: Optional[int]
    user_id: Optional[str]
    added_at: Optional[date]
    current_value: Optional[float]
    unrealized_pnl: Optional[float]

class PortfolioHealth(BaseModel):
    total_value: float
    xirr: float
    health_score: float
    diversification_score: float
    risk_exposure: float
