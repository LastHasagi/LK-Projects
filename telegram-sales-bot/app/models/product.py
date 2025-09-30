from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    currency = Column(String, default="BRL")
    is_active = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=-1)  # -1 means unlimited
    telegram_group_id = Column(String)  # Telegram group/channel ID for access
    access_duration_hours = Column(Integer, default=0)  # 0 means permanent access
    
    # Relationships
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    
    @property
    def main_image(self):
        """Get the main product image"""
        for image in self.images:
            if image.is_main:
                return image
        return self.images[0] if self.images else None
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity == -1 or self.stock_quantity > 0
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"


class ProductImage(Base, TimestampMixin):
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String, nullable=False)
    caption = Column(Text)
    is_main = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    
    # Relationships
    product = relationship("Product", back_populates="images")
    
    def __repr__(self):
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, is_main={self.is_main})>"
