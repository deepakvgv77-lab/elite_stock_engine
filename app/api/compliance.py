from fastapi import APIRouter, Body
from app.compliance.guardrails import GuardrailPolicies
from app.compliance.modes import router as modes_router

router = APIRouter()
guardrails = GuardrailPolicies()

router.include_router(modes_router, prefix="/mode", tags=["Compliance"])

@router.post("/validate")
async def validate_trade(trade: dict = Body(...)):
    allowed = guardrails.validate(trade)
    return {"allowed": allowed}
