from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import hmac
import hashlib
from loguru import logger

from app.config import get_settings
from app.database import get_async_session
from app.services.payment_service import PaymentService
from app.services.order_service import OrderService
from app.services.access_service import AccessService
from app.services.telegram_service import TelegramService

settings = get_settings()
router = APIRouter()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@router.post("/payment/mercadopago")
async def mercadopago_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Handle MercadoPago webhook"""
    try:
        # Get webhook data
        webhook_data = await request.json()
        logger.info(f"MercadoPago webhook received: {webhook_data}")
        
        # Verify signature if configured
        if settings.mercadopago_webhook_secret:
            signature = request.headers.get("X-Signature")
            if not signature:
                raise HTTPException(status_code=401, detail="Missing signature")
            
            payload = await request.body()
            if not verify_webhook_signature(payload, signature, settings.mercadopago_webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process webhook
        payment_service = PaymentService()
        order_service = OrderService(db)
        access_service = AccessService(db)
        
        # Get payment info
        if webhook_data.get("type") == "payment":
            payment_id = webhook_data.get("data", {}).get("id")
            
            # Get payment from MercadoPago
            payment_data = await payment_service.get_payment_details(payment_id)
            
            if payment_data:
                # Find order by external reference
                order_number = payment_data.get("external_reference")
                order = await order_service.get_order_by_number(order_number)
                
                if order and payment_data.get("status") == "approved":
                    # Update order status
                    await order_service.mark_as_paid(order.id)
                    
                    # Create access
                    access = await access_service.create_access(order)
                    
                    # Send access link via Telegram
                    from app.main import telegram_service
                    await telegram_service.send_access_link(
                        order.user.telegram_id,
                        access,
                        order
                    )
                    
                    logger.info(f"Payment approved for order {order_number}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing MercadoPago webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/payment/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Handle Stripe webhook"""
    # Similar implementation for Stripe
    return {"status": "ok"}


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook for production"""
    try:
        from app.main import telegram_service
        
        # Get update data
        update_data = await request.json()
        
        # Process update
        await telegram_service.app.process_update(update_data)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
