# Phase 031: Authentication

## Objective

Implement JWT authentication with rolling window expiry and HTTP Bearer security.

## Prerequisites

- Phase 030 completed
- `backend/src/backend/settings.py` and `models.py` exist

## Steps

### 3.1: Implement auth.py (JWT Authentication)

**Key Implementation**: JWT tokens have a **rolling window** — each successful use extends expiry to 7 days from now.

Create `backend/src/backend/auth.py`:

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

from .settings import settings
from .models import TokenData

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with rolling window expiry.
    
    Tokens expire in 7 days. Each use extends the expiry to 7 days from now.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_expiration_days
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Verify JWT token and refresh expiry on each use (rolling window).
    
    If token is valid, refresh it to expire 7 days from now.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        token_data = TokenData(sub=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return token_data.sub


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user against configured credentials."""
    return (
        username == settings.app_username
        and password == settings.app_password
    )
```

### 3.2: Implement routers/auth.py (Authentication Routes)

Create `backend/src/backend/routers/auth.py`:

```python
from fastapi import APIRouter, HTTPException, status, Depends
from ..models import LoginRequest, LoginResponse
from ..auth import authenticate_user, create_access_token, verify_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with username and password."""
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    access_token = create_access_token(data={"sub": request.username})
    return LoginResponse(access_token=access_token)


@router.post("/logout")
async def logout():
    """Logout (client-side token removal)."""
    return {"message": "Logged out successfully"}


@router.get("/verify")
async def verify(username: str = Depends(verify_token)):
    """Verify current token."""
    return {"username": username}
```

---

## Verification Checklist

- [ ] `backend/src/backend/auth.py` created
- [ ] `backend/src/backend/routers/auth.py` created
- [ ] JWT token creation works
- [ ] Token verification works
- [ ] User authentication against credentials works

## Next Step

Proceed to [032-database-wrapper.md](./032-database-wrapper.md)
