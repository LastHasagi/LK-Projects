from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import string

from app.models.access import Access, AccessLog
from app.models.order import Order
from app.models.product import Product


class AccessService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_access(self, order: Order) -> Access:
        """Create access for paid order"""
        # Generate unique access token
        access_token = self._generate_access_token()
        
        # Get product details
        product = order.items[0].product  # Assuming single product per order for now
        
        # Calculate expiry date
        expires_at = None
        if product.access_duration_hours > 0:
            expires_at = datetime.utcnow() + timedelta(hours=product.access_duration_hours)
        
        access = Access(
            user_id=order.user_id,
            order_id=order.id,
            telegram_group_id=product.telegram_group_id,
            access_token=access_token,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(access)
        await self.db.commit()
        await self.db.refresh(access)
        
        # Log access creation
        await self.log_access(access.id, "created", "Access created after payment")
        
        return access
    
    async def get_access(self, access_id: int) -> Optional[Access]:
        """Get access by ID"""
        result = await self.db.execute(
            select(Access).where(Access.id == access_id)
        )
        return result.scalar_one_or_none()
    
    async def get_access_by_token(self, token: str) -> Optional[Access]:
        """Get access by token"""
        result = await self.db.execute(
            select(Access).where(Access.access_token == token)
        )
        return result.scalar_one_or_none()
    
    async def get_user_accesses(self, user_id: int) -> List[Access]:
        """Get all accesses for a user"""
        result = await self.db.execute(
            select(Access)
            .where(Access.user_id == user_id)
            .order_by(Access.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_active_accesses(self, telegram_group_id: str) -> List[Access]:
        """Get active accesses for a group"""
        result = await self.db.execute(
            select(Access)
            .where(
                and_(
                    Access.telegram_group_id == telegram_group_id,
                    Access.is_active == True,
                    Access.revoked_at.is_(None)
                )
            )
        )
        
        # Filter out expired accesses
        accesses = result.scalars().all()
        return [a for a in accesses if a.is_valid]
    
    async def validate_access(self, access_token: str) -> Optional[Access]:
        """Validate access token"""
        access = await self.get_access_by_token(access_token)
        
        if not access or not access.is_valid:
            return None
        
        await self.log_access(access.id, "validated", "Access token validated")
        return access
    
    async def revoke_access(self, access_id: int, reason: str = None) -> bool:
        """Revoke access"""
        access = await self.get_access(access_id)
        if not access:
            return False
        
        access.revoke(reason)
        await self.db.commit()
        
        await self.log_access(access_id, "revoked", f"Access revoked: {reason}")
        return True
    
    async def extend_access(self, access_id: int, hours: int) -> Optional[Access]:
        """Extend access duration"""
        access = await self.get_access(access_id)
        if not access:
            return None
        
        if access.expires_at:
            # Extend from current expiry or now, whichever is later
            base_time = max(access.expires_at, datetime.utcnow())
            access.expires_at = base_time + timedelta(hours=hours)
        else:
            # Set new expiry
            access.expires_at = datetime.utcnow() + timedelta(hours=hours)
        
        await self.db.commit()
        await self.db.refresh(access)
        
        await self.log_access(access_id, "extended", f"Access extended by {hours} hours")
        return access
    
    async def get_expiring_accesses(self, hours: int = 24) -> List[Access]:
        """Get accesses expiring within specified hours"""
        expiry_threshold = datetime.utcnow() + timedelta(hours=hours)
        
        result = await self.db.execute(
            select(Access)
            .where(
                and_(
                    Access.is_active == True,
                    Access.expires_at.isnot(None),
                    Access.expires_at <= expiry_threshold,
                    Access.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalars().all()
    
    async def get_expired_accesses(self) -> List[Access]:
        """Get expired but still active accesses"""
        result = await self.db.execute(
            select(Access)
            .where(
                and_(
                    Access.is_active == True,
                    Access.expires_at.isnot(None),
                    Access.expires_at <= datetime.utcnow()
                )
            )
        )
        return result.scalars().all()
    
    async def log_access(self, access_id: int, action: str, details: str = None) -> AccessLog:
        """Log access activity"""
        log = AccessLog(
            access_id=access_id,
            action=action,
            details=details
        )
        
        self.db.add(log)
        await self.db.commit()
        return log
    
    async def update_invite_link(self, access_id: int, invite_link: str) -> bool:
        """Update invite link for access"""
        access = await self.get_access(access_id)
        if not access:
            return False
        
        access.invite_link = invite_link
        await self.db.commit()
        
        await self.log_access(access_id, "invite_link_updated", "Invite link generated")
        return True
    
    def _generate_access_token(self) -> str:
        """Generate unique access token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
