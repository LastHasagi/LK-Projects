import mercadopago
from typing import Dict, Any, Optional
import qrcode
import io
import base64
from datetime import datetime, timedelta
import uuid
from loguru import logger

from app.config import get_settings
from app.models.payment import Payment, PaymentStatus, PaymentMethod, PaymentGateway
from app.models.order import Order


class PaymentService:
    def __init__(self):
        self.settings = get_settings()
        self.mp_client = None
        
        if self.settings.mercadopago_access_token:
            self.mp_client = mercadopago.SDK(self.settings.mercadopago_access_token)
    
    async def create_payment(self, order: Order, payment_method: PaymentMethod) -> Payment:
        """Create a payment for an order"""
        payment = Payment(
            order_id=order.id,
            payment_method=payment_method,
            payment_gateway=PaymentGateway.MERCADOPAGO,
            amount=order.total_amount,
            currency=order.currency,
            status=PaymentStatus.PENDING
        )
        
        if payment_method == PaymentMethod.PIX:
            payment_data = await self._create_pix_payment(order)
            payment.gateway_payment_id = payment_data.get("id")
            payment.pix_qr_code = payment_data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code")
            payment.pix_copy_paste = payment_data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code")
            payment.pix_qr_code_base64 = await self._generate_qr_code(payment.pix_copy_paste)
            payment.gateway_response = payment_data
        
        elif payment_method == PaymentMethod.CREDIT_CARD:
            payment_data = await self._create_card_payment(order)
            payment.gateway_payment_id = payment_data.get("id")
            payment.gateway_response = payment_data
        
        return payment
    
    async def _create_pix_payment(self, order: Order) -> Dict[str, Any]:
        """Create PIX payment with Mercado Pago"""
        if not self.mp_client:
            raise ValueError("Mercado Pago not configured")
        
        payment_data = {
            "transaction_amount": float(order.total_amount),
            "description": f"Pedido #{order.order_number}",
            "payment_method_id": "pix",
            "payer": {
                "email": order.user.email or f"user{order.user.telegram_id}@telegram.com",
                "first_name": order.user.first_name or "Cliente",
                "last_name": order.user.last_name or "Telegram",
                "identification": {
                    "type": "CPF",
                    "number": "12345678909"  # This should come from user data
                }
            },
            "notification_url": f"{self.settings.telegram_webhook_url}/webhook/payment/mercadopago",
            "external_reference": order.order_number,
            "expires": True,
            "date_of_expiration": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }
        
        try:
            result = self.mp_client.payment().create(payment_data)
            if result["status"] == 201:
                return result["response"]
            else:
                logger.error(f"MercadoPago error: {result}")
                raise Exception(f"Payment creation failed: {result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error creating PIX payment: {e}")
            raise
    
    async def _create_card_payment(self, order: Order) -> Dict[str, Any]:
        """Create card payment checkout"""
        if not self.mp_client:
            raise ValueError("Mercado Pago not configured")
        
        # Create preference for checkout
        preference_data = {
            "items": [
                {
                    "title": f"Pedido #{order.order_number}",
                    "quantity": 1,
                    "unit_price": float(order.total_amount),
                    "currency_id": order.currency
                }
            ],
            "payer": {
                "email": order.user.email or f"user{order.user.telegram_id}@telegram.com",
                "name": order.user.first_name or "Cliente",
                "surname": order.user.last_name or "Telegram"
            },
            "back_urls": {
                "success": f"{self.settings.telegram_webhook_url}/payment/success",
                "failure": f"{self.settings.telegram_webhook_url}/payment/failure",
                "pending": f"{self.settings.telegram_webhook_url}/payment/pending"
            },
            "auto_return": "approved",
            "notification_url": f"{self.settings.telegram_webhook_url}/webhook/payment/mercadopago",
            "external_reference": order.order_number,
            "expires": True,
            "expiration_date_to": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        try:
            result = self.mp_client.preference().create(preference_data)
            if result["status"] == 201:
                return result["response"]
            else:
                logger.error(f"MercadoPago error: {result}")
                raise Exception(f"Preference creation failed: {result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error creating card payment: {e}")
            raise
    
    async def _generate_qr_code(self, data: str) -> str:
        """Generate QR code base64 image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def check_payment_status(self, payment: Payment) -> PaymentStatus:
        """Check payment status from gateway"""
        if not self.mp_client or not payment.gateway_payment_id:
            return payment.status
        
        try:
            result = self.mp_client.payment().get(payment.gateway_payment_id)
            if result["status"] == 200:
                mp_status = result["response"]["status"]
                
                status_mapping = {
                    "pending": PaymentStatus.PENDING,
                    "approved": PaymentStatus.APPROVED,
                    "authorized": PaymentStatus.APPROVED,
                    "in_process": PaymentStatus.PROCESSING,
                    "in_mediation": PaymentStatus.PROCESSING,
                    "rejected": PaymentStatus.REJECTED,
                    "cancelled": PaymentStatus.CANCELLED,
                    "refunded": PaymentStatus.REFUNDED,
                    "charged_back": PaymentStatus.REFUNDED
                }
                
                return status_mapping.get(mp_status, PaymentStatus.PENDING)
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return payment.status
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Optional[Payment]:
        """Process payment webhook from gateway"""
        try:
            # Validate webhook signature if configured
            if self.settings.mercadopago_webhook_secret:
                # TODO: Implement webhook signature validation
                pass
            
            # Get payment info from webhook
            payment_id = webhook_data.get("data", {}).get("id")
            if not payment_id:
                logger.warning(f"No payment ID in webhook: {webhook_data}")
                return None
            
            # Get payment details from MercadoPago
            result = self.mp_client.payment().get(payment_id)
            if result["status"] != 200:
                logger.error(f"Failed to get payment details: {result}")
                return None
            
            payment_data = result["response"]
            external_reference = payment_data.get("external_reference")
            
            # Find payment by order number
            # This would need database access - simplified for now
            # payment = await get_payment_by_order_number(external_reference)
            
            return None  # Placeholder
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return None
