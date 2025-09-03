# app/api/security.py
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from app.core.security import (
    authenticate_user,
    fake_users_db,
    create_access_token,
    create_device_token,
    verify_token as core_verify_token,
    get_current_user,
)
from app.core.config import settings

router = APIRouter()

# OAuth2 Password Grant token endpoint (Swagger Authorize uses this)
@router.post("/token", summary="Password grant: issue access token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Accepts form fields: username, password (and optionally client_id/client_secret).
    Returns: {"access_token": "<JWT>", "token_type": "bearer"}
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Include is_superuser in token for visibility; authorization still checks DB
    token = create_access_token(
        data={"sub": user.username, "is_superuser": getattr(user, "is_superuser", False)},
        expires_delta=expires
    )
    return {"access_token": token, "token_type": "bearer"}


# Optional: keep a device-token flow for custom use cases (JSON body)
@router.post("/device-token", summary="Issue device-specific token (expects JSON)")
async def generate_device_token(
    user: str = Body(..., embed=True),
    device: str = Body(..., embed=True)
):
    """
    Body example:
    {
      "user": "deepak_dheebu",
      "device": "my-laptop-uuid"
    }
    """
    return {"access_token": create_device_token(user, device)}


# Verify/inspect current Bearer token (useful for debugging)
oauth2_scheme_local = OAuth2PasswordBearer(tokenUrl="/api/v6/security/token", auto_error=False)

@router.get("/verify", summary="Decode current bearer token")
async def verify_token_route(token: Optional[str] = Depends(oauth2_scheme_local)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    payload = core_verify_token(token)
    return payload


# Handy endpoint to see the currently authenticated user
@router.get("/me", summary="Current user info")
async def read_me(current_user=Depends(get_current_user)):
    return {
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "disabled": current_user.disabled,
        "is_superuser": current_user.is_superuser,
    }
