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


class HomeSummary(BaseModel):
    """Summary statistics for the home page."""
    total_servers: int
    running_processes: int
    total_processes: int


class HomeResponse(BaseModel):
    """Response for the home page endpoint."""
    name: str
    version: str
    description: str
    summary: HomeSummary
    servers: list
    processes: list
