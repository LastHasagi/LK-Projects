from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime

from app.models.user import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_user(self, telegram_user_data: dict) -> User:
        """Get or create user from Telegram data"""
        telegram_id = telegram_user_data.get("id")
        
        # Try to find existing user
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update user info
            user.username = telegram_user_data.get("username", user.username)
            user.first_name = telegram_user_data.get("first_name", user.first_name)
            user.last_name = telegram_user_data.get("last_name", user.last_name)
            user.language_code = telegram_user_data.get("language_code", user.language_code)
        else:
            # Create new user
            user = User(
                telegram_id=telegram_id,
                username=telegram_user_data.get("username"),
                first_name=telegram_user_data.get("first_name"),
                last_name=telegram_user_data.get("last_name"),
                language_code=telegram_user_data.get("language_code", "pt-BR")
            )
            self.db.add(user)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users list"""
        result = await self.db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc())
        )
        return result.scalars().all()
    
    async def count_users(self) -> int:
        """Count total users"""
        result = await self.db.execute(
            select(func.count(User.id))
        )
        return result.scalar() or 0
    
    async def count_active_users(self) -> int:
        """Count active users"""
        result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        return result.scalar() or 0
    
    async def update_user(self, user_id: int, data: dict) -> Optional[User]:
        """Update user"""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user"""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        user.is_active = False
        await self.db.commit()
        return True
