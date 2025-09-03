# app/api/admin.py
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_superuser, fake_users_db, User

# Router is protected at the router level; all endpoints require superuser
router = APIRouter(
    dependencies=[Depends(get_current_superuser)]
)

@router.get("/info", summary="Admin: service info (admin-only)")
async def admin_info(current_admin: User = Depends(get_current_superuser)):
    return {
        "admin": current_admin.username,
        "role": "superuser",
        "message": "Welcome to the admin console"
    }

@router.get("/users", summary="Admin: list users (admin-only)")
async def list_users(_: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """
    Lists the users in the in-memory store. (No hashed passwords are returned.)
    Since you run a single super admin, this will return that one record.
    """
    users: List[Dict[str, Any]] = []
    for u in fake_users_db.values():
        users.append({
            "username": u["username"],
            "full_name": u.get("full_name"),
            "email": u.get("email"),
            "disabled": bool(u.get("disabled", False)),
            "is_superuser": bool(u.get("is_superuser", False)),
        })
    return {"count": len(users), "users": users}

@router.post("/echo", summary="Admin: echo payload (admin-only)")
async def echo_sample(payload: Dict[str, Any], _: User = Depends(get_current_superuser)):
    """
    Utility endpoint to confirm admin protection and test POST bodies.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")
    return {"received": payload}
