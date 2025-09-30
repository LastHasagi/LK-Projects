from sqlalchemy import Column, Integer, String, Text, Boolean, Enum
import enum
from .base import Base, TimestampMixin


class MessageType(enum.Enum):
    WELCOME = "welcome"
    PRODUCT_LIST = "product_list"
    ORDER_CONFIRMATION = "order_confirmation"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_APPROVED = "payment_approved"
    PAYMENT_REJECTED = "payment_rejected"
    ACCESS_GRANTED = "access_granted"
    ACCESS_EXPIRING = "access_expiring"
    ACCESS_EXPIRED = "access_expired"
    REMINDER_1 = "reminder_1"
    REMINDER_2 = "reminder_2"
    REMINDER_3 = "reminder_3"
    CUSTOM = "custom"


class MessageTemplate(Base, TimestampMixin):
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(Enum(MessageType), nullable=False)
    subject = Column(String)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    language = Column(String, default="pt-BR")
    
    # Variables that can be used in template
    # {user_name}, {product_name}, {order_number}, {payment_link}, {access_link}, etc.
    available_variables = Column(Text)
    
    def render(self, **kwargs):
        """Render template with variables"""
        content = self.content
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in content:
                content = content.replace(placeholder, str(value))
        return content
    
    def __repr__(self):
        return f"<MessageTemplate(id={self.id}, name={self.name}, type={self.type.value})>"
