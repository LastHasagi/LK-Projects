from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    email = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    language_code = Column(String, default="pt-BR")
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    accesses = relationship("Access", back_populates="user")
    
    @property
    def full_name(self):
        """Get user's full name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.username or f"User {self.telegram_id}"
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
