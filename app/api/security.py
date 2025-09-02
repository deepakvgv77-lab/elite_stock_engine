from fastapi import APIRouter, Depends, Body
from app.security.auth import create_device_token, verify_token

router = APIRouter()

@router.post("/token")
async def generate_token(user: str = Body(...), device: str = Body(...)):
    return {"access_token": create_device_token(user, device)}

@router.get("/verify")
async def verify_token_route(token=Depends(verify_token)):
    return token
