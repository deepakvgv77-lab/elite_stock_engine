from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/mode")
async def get_compliance_mode(sebi_mode: bool = Query(True)):
    return {"mode": "SEBI" if sebi_mode else "STANDARD"}
