"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from ..models.auth import LoginRequest, TokenResponse
from ..services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """User login"""
    token = AuthService.authenticate(credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return TokenResponse(access_token=token, token_type="bearer")
