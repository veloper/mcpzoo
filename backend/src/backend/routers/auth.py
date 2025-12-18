from fastapi import APIRouter, HTTPException, status, Depends
from src.backend.models import LoginRequest, LoginResponse
from src.backend.auth import authenticate_user, create_access_token, verify_token

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
