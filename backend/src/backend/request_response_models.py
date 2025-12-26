from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token data."""
    sub: str | None = None
    exp: int | None = None
