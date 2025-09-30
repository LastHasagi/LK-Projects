from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    unit_price: float
    subtotal: float
    product_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    id: int
    order_number: str
    user_id: int
    status: OrderStatus
    total_amount: float
    currency: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    user_name: Optional[str] = None
    payment_status: Optional[str] = None
    
    class Config:
        from_attributes = True
