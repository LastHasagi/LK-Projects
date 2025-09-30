from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PaymentMethod(str, Enum):
    PIX = "pix"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BOLETO = "boleto"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentGateway(str, Enum):
    MERCADOPAGO = "mercadopago"
    STRIPE = "stripe"
    PAGSEGURO = "pagseguro"


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    payment_method: PaymentMethod
    payment_gateway: PaymentGateway
    status: PaymentStatus
    amount: float
    currency: str
    gateway_payment_id: Optional[str] = None
    pix_qr_code: Optional[str] = None
    pix_qr_code_base64: Optional[str] = None
    pix_copy_paste: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
