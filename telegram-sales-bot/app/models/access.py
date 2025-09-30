from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from .base import Base, TimestampMixin


class Access(Base, TimestampMixin):
    __tablename__ = "accesses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    telegram_group_id = Column(String, nullable=False)
    access_token = Column(String, unique=True, index=True, nullable=False)
    invite_link = Column(String)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
    revoke_reason = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="accesses")
    order = relationship("Order")
    logs = relationship("AccessLog", back_populates="access", cascade="all, delete-orphan")
    
    @property
    def is_expired(self):
        """Check if access is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if access is valid"""
        return self.is_active and not self.is_expired and not self.revoked_at
    
    def revoke(self, reason: str = None):
        """Revoke access"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revoke_reason = reason
    
    def __repr__(self):
        return f"<Access(id={self.id}, user_id={self.user_id}, is_valid={self.is_valid})>"


class AccessLog(Base, TimestampMixin):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    access_id = Column(Integer, ForeignKey("accesses.id"), nullable=False)
    action = Column(String, nullable=False)  # joined, left, kicked, etc.
    details = Column(Text)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Relationships
    access = relationship("Access", back_populates="logs")
    
    def __repr__(self):
        return f"<AccessLog(id={self.id}, access_id={self.access_id}, action={self.action})>"
