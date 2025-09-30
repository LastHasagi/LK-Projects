from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum
from .base import Base, TimestampMixin


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="BRL")
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)
    
    @property
    def is_paid(self):
        """Check if order is paid"""
        return self.status == OrderStatus.PAID
    
    def calculate_total(self):
        """Calculate total order amount"""
        total = sum(item.subtotal for item in self.items)
        self.total_amount = total
        return total
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status.value})>"


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    def calculate_subtotal(self):
        """Calculate item subtotal"""
        self.subtotal = self.quantity * self.unit_price
        return self.subtotal
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"
