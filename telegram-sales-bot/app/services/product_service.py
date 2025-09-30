from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any

from app.models.product import Product, ProductImage


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_product(self, data: Dict[str, Any]) -> Product:
        """Create new product"""
        images_data = data.pop("images", [])
        
        product = Product(**data)
        self.db.add(product)
        await self.db.flush()
        
        # Add images
        for img_data in images_data:
            image = ProductImage(product_id=product.id, **img_data)
            self.db.add(image)
        
        await self.db.commit()
        await self.db.refresh(product)
        return product
    
    async def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.images))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Product]:
        """Get products list"""
        query = select(Product).options(selectinload(Product.images))
        
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
        
        result = await self.db.execute(
            query.order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_all_products(self) -> List[Product]:
        """Get all products"""
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.images))
            .order_by(Product.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_active_products(self) -> List[Product]:
        """Get active products with stock"""
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.images))
            .where(Product.is_active == True)
            .where((Product.stock_quantity > 0) | (Product.stock_quantity == -1))
            .order_by(Product.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_product(self, product_id: int, data: Dict[str, Any]) -> Optional[Product]:
        """Update product"""
        product = await self.get_product(product_id)
        if not product:
            return None
        
        images_data = data.pop("images", None)
        
        # Update product fields
        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        # Update images if provided
        if images_data is not None:
            # Remove old images
            for image in product.images:
                await self.db.delete(image)
            
            # Add new images
            for img_data in images_data:
                image = ProductImage(product_id=product.id, **img_data)
                self.db.add(image)
        
        await self.db.commit()
        await self.db.refresh(product)
        return product
    
    async def delete_product(self, product_id: int) -> bool:
        """Delete product"""
        product = await self.get_product(product_id)
        if not product:
            return False
        
        await self.db.delete(product)
        await self.db.commit()
        return True
    
    async def decrease_stock(self, product_id: int, quantity: int = 1) -> bool:
        """Decrease product stock"""
        product = await self.get_product(product_id)
        if not product:
            return False
        
        if product.stock_quantity == -1:  # Unlimited stock
            return True
        
        if product.stock_quantity < quantity:
            return False
        
        product.stock_quantity -= quantity
        await self.db.commit()
        return True
    
    async def count_products(self, is_active: Optional[bool] = None) -> int:
        """Count products"""
        query = select(func.count(Product.id))
        
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
