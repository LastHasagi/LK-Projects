from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os

from app.config import get_settings
from app.database import get_async_session
# Auth removed for direct access
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.services.user_service import UserService
from app.services.message_service import MessageService

settings = get_settings()
router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Admin dashboard"""
    # Get statistics
    product_service = ProductService(db)
    order_service = OrderService(db)
    user_service = UserService(db)
    
    stats = {
        "total_products": await product_service.count_products(),
        "total_orders": await order_service.count_orders(),
        "total_users": await user_service.count_users(),
        "pending_orders": await order_service.count_pending_orders(),
        "revenue": await order_service.get_total_revenue()
    }
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": {"username": "admin"},
            "stats": stats
        }
    )


@router.get("/products", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Products management page"""
    product_service = ProductService(db)
    products = await product_service.get_all_products()
    
    return templates.TemplateResponse(
        "admin/products.html",
        {
            "request": request,
            "user": {"username": "admin"},
            "products": products
        }
    )


@router.get("/products/new", response_class=HTMLResponse)
async def new_product_form(
    request: Request,
):
    """New product form"""
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "user": {"username": "admin"},
            "product": None
        }
    )


@router.post("/products/new")
async def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    stock_quantity: int = Form(-1),
    telegram_group_id: str = Form(None),
    access_duration_hours: int = Form(0),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_async_session)
):
    """Create new product"""
    product_service = ProductService(db)
    
    # Handle image upload
    image_url = None
    if image and image.filename:
        # Save image
        file_extension = os.path.splitext(image.filename)[1]
        if file_extension.lower() in settings.allowed_extensions:
            file_name = f"product_{name.replace(' ', '_')}_{image.filename}"
            file_path = os.path.join(settings.upload_folder, file_name)
            
            with open(file_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            image_url = f"/uploads/{file_name}"
    
    # Create product
    product_data = {
        "name": name,
        "description": description,
        "price": price,
        "stock_quantity": stock_quantity,
        "telegram_group_id": telegram_group_id,
        "access_duration_hours": access_duration_hours
    }
    
    if image_url:
        product_data["images"] = [{"image_url": image_url, "is_main": True}]
    
    await product_service.create_product(product_data)
    
    return RedirectResponse(url="/admin/products", status_code=303)


@router.get("/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Orders management page"""
    order_service = OrderService(db)
    orders = await order_service.get_orders(status=status)
    
    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "user": {"username": "admin"},
            "orders": orders,
            "filter_status": status
        }
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Users management page"""
    user_service = UserService(db)
    users = await user_service.get_all_users()
    
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": {"username": "admin"},
            "users": users
        }
    )


@router.get("/messages", response_class=HTMLResponse)
async def admin_messages(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Message templates management page"""
    message_service = MessageService(db)
    templates_list = await message_service.get_all_templates()
    
    return templates.TemplateResponse(
        "admin/messages.html",
        {
            "request": request,
            "user": {"username": "admin"},
            "message_templates": templates_list
        }
    )


@router.get("/messages/{template_id}/edit", response_class=HTMLResponse)
async def edit_message_template(
    request: Request,
    template_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Edit message template"""
    message_service = MessageService(db)
    template = await message_service.get_template(template_id)
    
    return templates.TemplateResponse(
        "admin/message_form.html",
        {
            "request": request,
            "user": {"username": "admin"},
            "template": template
        }
    )


@router.post("/messages/{template_id}/edit")
async def update_message_template(
    template_id: int,
    content: str = Form(...),
    subject: Optional[str] = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_async_session)
):
    """Update message template"""
    message_service = MessageService(db)
    await message_service.update_template(
        template_id,
        {
            "content": content,
            "subject": subject,
            "is_active": is_active
        }
    )
    
    return RedirectResponse(url="/admin/messages", status_code=303)


@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Settings page"""
    # Get all settings from database
    # Simplified for now
    
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "user": {"username": "admin"},
            "settings": {}
        }
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request}
    )
