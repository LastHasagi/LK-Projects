from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_async_session
from app.routers.auth import get_current_admin_user
from app.schemas.auth import TokenData
from app.schemas.product import ProductResponse, ProductCreate, ProductUpdate
from app.schemas.order import OrderResponse
from app.schemas.user import UserResponse
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.services.user_service import UserService

router = APIRouter()


@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Get products list"""
    product_service = ProductService(db)
    return await product_service.get_products(skip=skip, limit=limit, is_active=is_active)


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get product by ID"""
    product_service = ProductService(db)
    product = await product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    current_user: TokenData = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create new product"""
    product_service = ProductService(db)
    return await product_service.create_product(product.dict())


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    current_user: TokenData = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update product"""
    product_service = ProductService(db)
    updated_product = await product_service.update_product(product_id, product.dict(exclude_unset=True))
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: TokenData = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete product"""
    product_service = ProductService(db)
    success = await product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get orders list"""
    order_service = OrderService(db)
    return await order_service.get_orders(
        skip=skip,
        limit=limit,
        status=status,
        user_id=user_id
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: TokenData = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get order by ID"""
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: TokenData = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get users list"""
    user_service = UserService(db)
    return await user_service.get_users(skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: TokenData = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get user by ID"""
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/stats")
async def get_stats(
    current_user: TokenData = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get statistics"""
    product_service = ProductService(db)
    order_service = OrderService(db)
    user_service = UserService(db)
    
    return {
        "products": {
            "total": await product_service.count_products(),
            "active": await product_service.count_products(is_active=True)
        },
        "orders": {
            "total": await order_service.count_orders(),
            "pending": await order_service.count_pending_orders(),
            "paid": await order_service.count_paid_orders()
        },
        "users": {
            "total": await user_service.count_users(),
            "active": await user_service.count_active_users()
        },
        "revenue": {
            "total": await order_service.get_total_revenue(),
            "monthly": await order_service.get_monthly_revenue()
        }
    }
