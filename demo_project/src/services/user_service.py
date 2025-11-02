"""
User business logic
"""
from typing import List, Optional
from ..models.user import User, UserCreate
from ..database import get_db_session

class UserService:
    @staticmethod
    def get_all_users() -> List[User]:
        """Get all users from database"""
        # TODO: Implement database query
        return []
    
    @staticmethod  
    def create_user(user_data: UserCreate) -> User:
        """Create a new user"""
        # TODO: Hash password and save to database
        pass
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        # TODO: Implement database query
        return None
