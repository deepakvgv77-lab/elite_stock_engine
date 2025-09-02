from fastapi import APIRouter, Body
from app.lineage.provenance import LineageEmitter

router = APIRouter()
emitter = LineageEmitter()

@router.post("/emit")
async def emit_lineage(event: dict = Body(...)):
    emitter.emit_event(**event)
    return {"status": "emitted"}
