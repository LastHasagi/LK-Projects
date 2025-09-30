from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any

from app.models.message_template import MessageTemplate, MessageType
from app.models.user import User
from app.models.order import Order
from app.models.product import Product


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_template(self, template_id: int) -> Optional[MessageTemplate]:
        """Get message template by ID"""
        result = await self.db.execute(
            select(MessageTemplate).where(MessageTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_template_by_type(self, message_type: MessageType, language: str = "pt-BR") -> Optional[MessageTemplate]:
        """Get message template by type and language"""
        result = await self.db.execute(
            select(MessageTemplate)
            .where(
                MessageTemplate.type == message_type,
                MessageTemplate.language == language,
                MessageTemplate.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_templates(self) -> List[MessageTemplate]:
        """Get all message templates"""
        result = await self.db.execute(
            select(MessageTemplate).order_by(MessageTemplate.type, MessageTemplate.language)
        )
        return result.scalars().all()
    
    async def create_template(self, data: Dict[str, Any]) -> MessageTemplate:
        """Create new message template"""
        template = MessageTemplate(**data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def update_template(self, template_id: int, data: Dict[str, Any]) -> Optional[MessageTemplate]:
        """Update message template"""
        template = await self.get_template(template_id)
        if not template:
            return None
        
        for key, value in data.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def render_welcome_message(self, user: User) -> str:
        """Render welcome message for user"""
        template = await self.get_template_by_type(MessageType.WELCOME, user.language_code)
        if not template:
            return f"Olá {user.full_name}! Bem-vindo ao nosso bot de vendas."
        
        return template.render(
            user_name=user.full_name,
            first_name=user.first_name or "Cliente"
        )
    
    async def render_order_confirmation(self, order: Order) -> str:
        """Render order confirmation message"""
        user = order.user
        template = await self.get_template_by_type(MessageType.ORDER_CONFIRMATION, user.language_code)
        
        if not template:
            return f"Pedido #{order.order_number} criado com sucesso! Total: R$ {order.total_amount:.2f}"
        
        products = ", ".join([item.product.name for item in order.items])
        
        return template.render(
            user_name=user.full_name,
            order_number=order.order_number,
            total_amount=f"R$ {order.total_amount:.2f}",
            products=products
        )
    
    async def render_payment_pending(self, order: Order, payment_method: str, payment_details: Dict[str, Any]) -> str:
        """Render payment pending message"""
        user = order.user
        template = await self.get_template_by_type(MessageType.PAYMENT_PENDING, user.language_code)
        
        if not template:
            return "Aguardando pagamento..."
        
        return template.render(
            user_name=user.full_name,
            order_number=order.order_number,
            total_amount=f"R$ {order.total_amount:.2f}",
            payment_method=payment_method,
            **payment_details
        )
    
    async def render_payment_approved(self, order: Order, access_link: str) -> str:
        """Render payment approved message"""
        user = order.user
        template = await self.get_template_by_type(MessageType.PAYMENT_APPROVED, user.language_code)
        
        if not template:
            return f"Pagamento aprovado! Seu link de acesso: {access_link}"
        
        return template.render(
            user_name=user.full_name,
            order_number=order.order_number,
            access_link=access_link
        )
    
    async def render_reminder(self, user: User, order: Order, reminder_number: int) -> str:
        """Render payment reminder message"""
        reminder_type = getattr(MessageType, f"REMINDER_{reminder_number}", MessageType.REMINDER_1)
        template = await self.get_template_by_type(reminder_type, user.language_code)
        
        if not template:
            return f"Lembrete: Seu pedido #{order.order_number} está aguardando pagamento."
        
        return template.render(
            user_name=user.full_name,
            order_number=order.order_number,
            total_amount=f"R$ {order.total_amount:.2f}"
        )
    
    async def initialize_default_templates(self):
        """Create default message templates"""
        default_templates = [
            {
                "name": "welcome_pt",
                "type": MessageType.WELCOME,
                "subject": "Bem-vindo!",
                "content": "Olá {first_name}! 👋\n\nBem-vindo ao nosso Bot de Vendas!\n\nAqui você pode:\n📦 Ver nossos produtos\n🛒 Fazer pedidos\n💳 Pagar com segurança\n🔐 Receber acesso instantâneo\n\nComo posso ajudá-lo hoje?",
                "language": "pt-BR",
                "available_variables": "user_name, first_name"
            },
            {
                "name": "order_confirmation_pt",
                "type": MessageType.ORDER_CONFIRMATION,
                "subject": "Pedido Confirmado",
                "content": "✅ *Pedido Confirmado!*\n\nOlá {user_name},\n\nSeu pedido *#{order_number}* foi criado com sucesso!\n\n📦 *Produtos:* {products}\n💰 *Total:* {total_amount}\n\nAgora escolha sua forma de pagamento para finalizar.",
                "language": "pt-BR",
                "available_variables": "user_name, order_number, total_amount, products"
            },
            {
                "name": "payment_pending_pix_pt",
                "type": MessageType.PAYMENT_PENDING,
                "subject": "Aguardando Pagamento PIX",
                "content": "🔐 *Pagamento via PIX*\n\nPedido: *#{order_number}*\nValor: *{total_amount}*\n\n📱 *Instruções:*\n1. Copie o código PIX abaixo\n2. Abra seu app bancário\n3. Faça o pagamento\n\n```\n{pix_code}\n```\n\n⏱ Este código expira em 30 minutos.\n✅ Após o pagamento, você receberá o acesso automaticamente!",
                "language": "pt-BR",
                "available_variables": "user_name, order_number, total_amount, pix_code, qr_code"
            },
            {
                "name": "payment_approved_pt",
                "type": MessageType.PAYMENT_APPROVED,
                "subject": "Pagamento Aprovado!",
                "content": "🎉 *Pagamento Confirmado!*\n\nParabéns {user_name}!\n\nSeu pagamento do pedido *#{order_number}* foi aprovado com sucesso!\n\n🔗 *Seu Link de Acesso:*\n{access_link}\n\n⚠️ *IMPORTANTE:*\n• Este link é único e pessoal\n• Não compartilhe com outras pessoas\n• Guarde este link com segurança\n\nObrigado pela sua compra! 🙏",
                "language": "pt-BR",
                "available_variables": "user_name, order_number, access_link"
            },
            {
                "name": "reminder_1_pt",
                "type": MessageType.REMINDER_1,
                "subject": "Lembrete de Pagamento",
                "content": "⏰ *Lembrete de Pagamento*\n\nOlá {user_name}!\n\nVimos que seu pedido *#{order_number}* no valor de *{total_amount}* ainda está aguardando pagamento.\n\n💡 Não perca esta oportunidade!\n\nFinalize seu pagamento agora e garanta seu acesso. 🚀",
                "language": "pt-BR",
                "available_variables": "user_name, order_number, total_amount"
            }
        ]
        
        for template_data in default_templates:
            # Check if template already exists
            existing = await self.db.execute(
                select(MessageTemplate).where(
                    MessageTemplate.name == template_data["name"]
                )
            )
            if not existing.scalar_one_or_none():
                await self.create_template(template_data)
