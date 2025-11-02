"""
User API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models.user import User, UserCreate
from ..services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[User])
async def get_users():
    """Get all users"""
    return UserService.get_all_users()

@router.post("/", response_model=User)
async def create_user(user: UserCreate):
    """Create a new user"""
    return UserService.create_user(user)

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get user by ID"""
    user = UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
