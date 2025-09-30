from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    language_code: str = "pt-BR"


class UserCreate(UserBase):
    telegram_id: int


class UserUpdate(UserBase):
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    telegram_id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    full_name: str
    
    class Config:
        from_attributes = True
