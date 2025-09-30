from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
import enum
from .base import Base, TimestampMixin


class PaymentMethod(enum.Enum):
    PIX = "pix"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BOLETO = "boleto"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentGateway(enum.Enum):
    MERCADOPAGO = "mercadopago"
    STRIPE = "stripe"
    PAGSEGURO = "pagseguro"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_gateway = Column(Enum(PaymentGateway), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="BRL")
    
    # Gateway specific IDs
    gateway_payment_id = Column(String, index=True)  # ID from payment gateway
    gateway_transaction_id = Column(String)
    
    # PIX specific fields
    pix_qr_code = Column(Text)
    pix_qr_code_base64 = Column(Text)
    pix_copy_paste = Column(Text)
    
    # Additional data from gateway
    gateway_response = Column(JSON)
    webhook_data = Column(JSON)
    
    # Error handling
    error_message = Column(Text)
    
    # Relationships
    order = relationship("Order", back_populates="payment")
    
    @property
    def is_approved(self):
        """Check if payment is approved"""
        return self.status == PaymentStatus.APPROVED
    
    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, status={self.status.value})>"
