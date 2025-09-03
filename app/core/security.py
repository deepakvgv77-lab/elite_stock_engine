# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

# ---------------------------------------------------------------------
# Password hashing context
# ---------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------
# OAuth2 scheme for token extraction
# IMPORTANT: Must match the router mount in main.py
# app.include_router(security_router, prefix="/api/v6/security", ...)
# ---------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v6/security/token",
    auto_error=False  # allows public endpoints to skip auth when using a global guard
)

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------
class TokenData(BaseModel):
    username: Optional[str] = None
    device_id: Optional[str] = None
    is_superuser: bool = False

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    is_superuser: bool = True  # super admin by default for this single-user setup

class UserInDB(User):
    hashed_password: str

# ---------------------------------------------------------------------
# Single super admin user ONLY (per your request)
# You can optionally override via env (recommended in production).
# ---------------------------------------------------------------------
ADMIN_USERNAME = getattr(settings, "ADMIN_USERNAME", "deepak_dheebu")
ADMIN_PASSWORD = getattr(settings, "ADMIN_PASSWORD", "Tleindia@1")  # default as requested

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

# Hash the admin password at import time
_admin_hash = get_password_hash(ADMIN_PASSWORD)

# In-memory "DB" with only the super admin user
fake_users_db: Dict[str, Dict[str, Any]] = {
    ADMIN_USERNAME: {
        "username": ADMIN_USERNAME,
        "full_name": "Super Administrator",
        "email": f"{ADMIN_USERNAME}@example.com",
        "hashed_password": _admin_hash,
        "disabled": False,
        "is_superuser": True,
    }
}

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
def get_user(db: Dict[str, Any], username: str) -> Optional[UserInDB]:
    """Get user from database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(db: Dict[str, Any], username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user credentials."""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    Caller should include {"sub": <username>} in 'data'.
    You may also include 'is_superuser' for visibility/debugging.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_device_token(user_id: str, device_id: str) -> str:
    """Create device-specific token."""
    payload = {"sub": user_id, "dev": device_id}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

# ---------------------------------------------------------------------
# Dependencies for route protection
# ---------------------------------------------------------------------
async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token in Authorization header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        # On protected routes, token must exist
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        is_superuser_claim = bool(payload.get("is_superuser", False))
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, is_superuser=is_superuser_claim)
    except JWTError:
        raise credentials_exception

    user = get_user(fake_users_db, username=token_data.username)  # type: ignore[arg-type]
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is not disabled."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is a superuser (admin-only)."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

# ---------------------------------------------------------------------
# Refresh tokens (optional for future phases)
# ---------------------------------------------------------------------
def create_refresh_token(user_id: str) -> str:
    """Create refresh token for extended sessions."""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def validate_refresh_token(token: str) -> Optional[str]:
    """Validate refresh token and return user_id."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload.get("sub")
    except JWTError:
        return None

# ---------------------------------------------------------------------
# Phase-aware path-based guard (optional)
# ---------------------------------------------------------------------
class EliteSecurityConfig:
    """Security configuration by feature phase."""
    PHASE_1_ENDPOINTS = ["/quotes", "/universe", "/gold", "/refresh", "/health"]
    PHASE_2_ENDPOINTS = ["/screener", "/analytics", "/factors"]
    PHASE_3_ENDPOINTS = ["/portfolio", "/holdings", "/performance"]
    ADMIN_ENDPOINTS   = ["/admin", "/system", "/users"]

def get_endpoint_security_level(path: str) -> str:
    """Determine security level required for endpoint based on phases."""
    config = EliteSecurityConfig()
    if any(endpoint in path for endpoint in config.ADMIN_ENDPOINTS):
        return "superuser"
    elif any(endpoint in path for endpoint in config.PHASE_3_ENDPOINTS):
        return "active_user"
    elif any(endpoint in path for endpoint in config.PHASE_2_ENDPOINTS):
        return "authenticated"
    else:
        return "public"

async def validate_token_for_endpoint(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    Global guard example: attach with
    app.router.dependencies.append(Depends(validate_token_for_endpoint))
    Public endpoints will not require a token.
    """
    path = request.url.path
    security_level = get_endpoint_security_level(path)

    if security_level == "public":
        return None

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    current_user = await get_current_user(token)

    if security_level == "active_user" and current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    if security_level == "superuser":
        await get_current_superuser(current_user)

    return current_user
