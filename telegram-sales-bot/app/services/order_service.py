from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_order(self, user_id: int, items: List[Dict[str, Any]]) -> Order:
        """Create new order"""
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        order = Order(
            order_number=order_number,
            user_id=user_id,
            status=OrderStatus.PENDING,
            total_amount=0
        )
        self.db.add(order)
        await self.db.flush()
        
        total = 0
        for item_data in items:
            product = await self.db.get(Product, item_data["product_id"])
            if not product:
                continue
            
            quantity = item_data.get("quantity", 1)
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
                subtotal=product.price * quantity
            )
            self.db.add(order_item)
            total += order_item.subtotal
        
        order.total_amount = total
        await self.db.commit()
        await self.db.refresh(order)
        return order
    
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.user),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.payment)
            )
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by number"""
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.user),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.payment)
            )
            .where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()
    
    async def get_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Order]:
        """Get orders list"""
        query = select(Order).options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payment)
        )
        
        if status:
            try:
                status_enum = OrderStatus(status)
                query = query.where(Order.status == status_enum)
            except ValueError:
                pass
        
        if user_id:
            query = query.where(Order.user_id == user_id)
        
        result = await self.db.execute(
            query.order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_user_orders(self, user_telegram_id: int) -> List[Order]:
        """Get orders for a Telegram user"""
        result = await self.db.execute(
            select(Order)
            .join(User)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.payment)
            )
            .where(User.telegram_id == user_telegram_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_order_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        """Update order status"""
        order = await self.get_order(order_id)
        if not order:
            return None
        
        order.status = status
        await self.db.commit()
        await self.db.refresh(order)
        return order
    
    async def mark_as_paid(self, order_id: int) -> Optional[Order]:
        """Mark order as paid"""
        return await self.update_order_status(order_id, OrderStatus.PAID)
    
    async def cancel_order(self, order_id: int) -> Optional[Order]:
        """Cancel order"""
        order = await self.get_order(order_id)
        if not order:
            return None
        
        if order.status in [OrderStatus.PAID, OrderStatus.CANCELLED]:
            return None
        
        order.status = OrderStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(order)
        return order
    
    async def get_expired_orders(self, hours: int = 24) -> List[Order]:
        """Get expired pending orders"""
        expiry_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(Order)
            .where(
                and_(
                    Order.status == OrderStatus.PENDING,
                    Order.created_at < expiry_time
                )
            )
        )
        return result.scalars().all()
    
    async def count_orders(self) -> int:
        """Count total orders"""
        result = await self.db.execute(
            select(func.count(Order.id))
        )
        return result.scalar() or 0
    
    async def count_pending_orders(self) -> int:
        """Count pending orders"""
        result = await self.db.execute(
            select(func.count(Order.id))
            .where(Order.status == OrderStatus.PENDING)
        )
        return result.scalar() or 0
    
    async def count_paid_orders(self) -> int:
        """Count paid orders"""
        result = await self.db.execute(
            select(func.count(Order.id))
            .where(Order.status == OrderStatus.PAID)
        )
        return result.scalar() or 0
    
    async def get_total_revenue(self) -> float:
        """Get total revenue from paid orders"""
        result = await self.db.execute(
            select(func.sum(Order.total_amount))
            .where(Order.status == OrderStatus.PAID)
        )
        return result.scalar() or 0.0
    
    async def get_monthly_revenue(self) -> float:
        """Get current month revenue"""
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(func.sum(Order.total_amount))
            .where(
                and_(
                    Order.status == OrderStatus.PAID,
                    Order.created_at >= start_of_month
                )
            )
        )
        return result.scalar() or 0.0
