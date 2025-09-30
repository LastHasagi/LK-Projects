from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductImageBase(BaseModel):
    image_url: str
    caption: Optional[str] = None
    is_main: bool = False
    order: int = 0


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageResponse(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    currency: str = "BRL"
    is_active: bool = True
    stock_quantity: int = -1
    telegram_group_id: Optional[str] = None
    access_duration_hours: int = 0


class ProductCreate(ProductBase):
    images: List[ProductImageCreate] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    is_active: Optional[bool] = None
    stock_quantity: Optional[int] = None
    telegram_group_id: Optional[str] = None
    access_duration_hours: Optional[int] = None
    images: Optional[List[ProductImageCreate]] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    images: List[ProductImageResponse] = []
    
    class Config:
        from_attributes = True
