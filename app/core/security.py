from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    username: Optional[str] = None
    device_id: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# Fake users database for Phase 1 (replace with real DB in later phases)
fake_users_db = {
    "elite_user": {
        "username": "elite_user",
        "full_name": "Elite Screener User",
        "email": "user@elitescreener.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    },
    "demo_user": {
        "username": "demo_user",
        "full_name": "Demo User",
        "email": "demo@elitescreener.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

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
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_device_token(user_id: str, device_id: str) -> str:
    """Create device-specific token (from your existing auth.py)."""
    payload = {"sub": user_id, "dev": device_id}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload (from your existing auth.py)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (not disabled)."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current superuser (for admin operations in future phases)."""
    if current_user.username not in ["elite_user"]:  # Basic superuser check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def create_refresh_token(user_id: str) -> str:
    """Create refresh token for extended sessions (future Phase 6 feature)."""
    expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last longer
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

# Elite Screener specific security configurations
class EliteSecurityConfig:
    """Security configuration for Elite Screener phases."""
    
    # Phase 1: Basic authentication
    PHASE_1_ENDPOINTS = ["/quotes", "/universe", "/gold", "/refresh", "/health"]
    
    # Phase 2: Screener endpoints (require authentication)
    PHASE_2_ENDPOINTS = ["/screener", "/analytics", "/factors"]
    
    # Phase 3: Portfolio endpoints (require active user)
    PHASE_3_ENDPOINTS = ["/portfolio", "/holdings", "/performance"]
    
    # Phase 6: Admin endpoints (require superuser)
    ADMIN_ENDPOINTS = ["/admin", "/system", "/users"]

def get_endpoint_security_level(path: str) -> str:
    """Determine security level required for endpoint based on Elite Screener phases."""
    config = EliteSecurityConfig()
    
    if any(endpoint in path for endpoint in config.ADMIN_ENDPOINTS):
        return "superuser"
    elif any(endpoint in path for endpoint in config.PHASE_3_ENDPOINTS):
        return "active_user"
    elif any(endpoint in path for endpoint in config.PHASE_2_ENDPOINTS):
        return "authenticated"
    else:
        return "public"

# Token validation middleware for different security levels
async def validate_token_for_endpoint(
    path: str, 
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """Validate token based on endpoint security requirements."""
    security_level = get_endpoint_security_level(path)
    
    if security_level == "public":
        return None
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    current_user = await get_current_user(token)
    
    if security_level == "active_user" and current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    if security_level == "superuser":
        await get_current_superuser(current_user)
    
    return current_user
