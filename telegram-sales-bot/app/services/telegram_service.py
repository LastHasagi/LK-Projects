from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
from loguru import logger
import uuid

from app.config import get_settings
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.payment import PaymentMethod
from app.models.access import Access


class TelegramService:
    def __init__(self):
        self.settings = get_settings()
        self.app = None
        self.bot = None
        
    async def initialize(self):
        """Initialize Telegram bot"""
        self.app = Application.builder().token(self.settings.telegram_bot_token).build()
        self.bot = self.app.bot
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("produtos", self.products_command))
        self.app.add_handler(CommandHandler("pedidos", self.orders_command))
        self.app.add_handler(CommandHandler("ajuda", self.help_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Create or update user in database
        # This would need database access - simplified for now
        
        welcome_text = (
            f"Olá {user.first_name}! 👋\n\n"
            "Bem-vindo ao nosso Bot de Vendas!\n\n"
            "Use os comandos:\n"
            "📦 /produtos - Ver produtos disponíveis\n"
            "📋 /pedidos - Ver seus pedidos\n"
            "❓ /ajuda - Obter ajuda\n\n"
            "Como posso ajudá-lo hoje?"
        )
        
        keyboard = [
            [InlineKeyboardButton("📦 Ver Produtos", callback_data="show_products")],
            [InlineKeyboardButton("📋 Meus Pedidos", callback_data="my_orders")],
            [InlineKeyboardButton("❓ Ajuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def products_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /produtos command"""
        await self.show_products(update, context)
    
    async def show_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available products"""
        # Get products from database - simplified for now
        products = []  # This would come from database
        
        if not products:
            text = "Desculpe, não há produtos disponíveis no momento. 😔"
            if update.callback_query:
                await update.callback_query.message.reply_text(text)
            else:
                await update.message.reply_text(text)
            return
        
        # Show products carousel
        for product in products:
            await self.send_product(update, context, product)
    
    async def send_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE, product: Dict[str, Any]):
        """Send product information"""
        text = (
            f"*{product['name']}*\n\n"
            f"{product['description']}\n\n"
            f"💰 Preço: R$ {product['price']:.2f}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🛒 Comprar", callback_data=f"buy_{product['id']}")],
            [InlineKeyboardButton("ℹ️ Mais informações", callback_data=f"info_{product['id']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        chat_id = update.effective_chat.id
        
        if product.get('image_url'):
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=product['image_url'],
                caption=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "show_products":
            await self.show_products(update, context)
        
        elif data == "my_orders":
            await self.show_user_orders(update, context)
        
        elif data == "help":
            await self.send_help(update, context)
        
        elif data.startswith("buy_"):
            product_id = int(data.split("_")[1])
            await self.start_purchase(update, context, product_id)
        
        elif data.startswith("pay_"):
            parts = data.split("_")
            order_id = int(parts[1])
            payment_method = parts[2]
            await self.process_payment(update, context, order_id, payment_method)
        
        elif data.startswith("cancel_order_"):
            order_id = int(data.split("_")[2])
            await self.cancel_order(update, context, order_id)
    
    async def start_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
        """Start purchase process"""
        # Get product from database
        # Create order
        # Show payment options
        
        text = "Escolha a forma de pagamento:"
        
        keyboard = [
            [InlineKeyboardButton("💳 PIX", callback_data=f"pay_ORDER_ID_pix")],
            [InlineKeyboardButton("💳 Cartão de Crédito", callback_data=f"pay_ORDER_ID_credit_card")],
            [InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_order_ORDER_ID")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    
    async def process_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int, payment_method: str):
        """Process payment for order"""
        # Create payment
        # Send payment instructions
        
        if payment_method == "pix":
            await self.send_pix_payment(update, context, order_id)
        elif payment_method == "credit_card":
            await self.send_card_payment(update, context, order_id)
    
    async def send_pix_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
        """Send PIX payment instructions"""
        # Get payment details from payment service
        
        text = (
            "🔐 *Pagamento via PIX*\n\n"
            "Escaneie o QR Code ou copie o código PIX:\n\n"
            "```\n"
            "PIX_CODE_HERE\n"
            "```\n\n"
            "⏱ Este código expira em 30 minutos.\n"
            "✅ Após o pagamento, você receberá o acesso automaticamente!"
        )
        
        # Send QR code image if available
        await update.callback_query.message.reply_text(text, parse_mode='Markdown')
    
    async def send_access_link(self, user_telegram_id: int, access: Access, order: Order):
        """Send access link to user after payment confirmation"""
        try:
            # Generate unique invite link
            invite_link = await self.create_invite_link(
                access.telegram_group_id,
                access.expires_at
            )
            
            text = (
                "🎉 *Pagamento Confirmado!*\n\n"
                f"Seu pedido #{order.order_number} foi aprovado!\n\n"
                "🔗 *Link de Acesso:*\n"
                f"{invite_link}\n\n"
                "⚠️ *IMPORTANTE:*\n"
                "• Este link é único e pessoal\n"
                "• Não compartilhe com outras pessoas\n"
            )
            
            if access.expires_at:
                text += f"• Válido até: {access.expires_at.strftime('%d/%m/%Y %H:%M')}\n"
            
            await self.bot.send_message(
                chat_id=user_telegram_id,
                text=text,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending access link: {e}")
            return False
    
    async def create_invite_link(self, chat_id: str, expire_date: Optional[datetime] = None) -> str:
        """Create invite link for Telegram group/channel"""
        try:
            kwargs = {
                "chat_id": chat_id,
                "member_limit": 1,  # Single use link
                "creates_join_request": False
            }
            
            if expire_date:
                kwargs["expire_date"] = expire_date
            
            result = await self.bot.create_chat_invite_link(**kwargs)
            return result.invite_link
            
        except TelegramError as e:
            logger.error(f"Error creating invite link: {e}")
            raise
    
    async def send_reminder(self, user_telegram_id: int, message: str):
        """Send reminder message to user"""
        try:
            await self.bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            return False
    
    async def check_user_in_group(self, user_telegram_id: int, group_id: str) -> bool:
        """Check if user is in a group"""
        try:
            member = await self.bot.get_chat_member(chat_id=group_id, user_id=user_telegram_id)
            return member.status in ['member', 'administrator', 'creator']
        except:
            return False
    
    async def remove_user_from_group(self, user_telegram_id: int, group_id: str) -> bool:
        """Remove user from group"""
        try:
            await self.bot.ban_chat_member(
                chat_id=group_id,
                user_id=user_telegram_id,
                until_date=datetime.now() + timedelta(seconds=30)
            )
            return True
        except Exception as e:
            logger.error(f"Error removing user from group: {e}")
            return False
    
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pedidos command"""
        await self.show_user_orders(update, context)
    
    async def show_user_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user orders"""
        user_telegram_id = update.effective_user.id
        
        # Get orders from database - simplified for now
        orders = []
        
        if not orders:
            text = "Você ainda não tem pedidos. 📦"
        else:
            text = "*Seus Pedidos:*\n\n"
            for order in orders:
                text += f"📦 Pedido #{order['number']} - {order['status']}\n"
        
        if update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ajuda command"""
        await self.send_help(update, context)
    
    async def send_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        help_text = (
            "*Central de Ajuda* ❓\n\n"
            "*Comandos disponíveis:*\n"
            "/start - Iniciar o bot\n"
            "/produtos - Ver produtos\n"
            "/pedidos - Ver seus pedidos\n"
            "/ajuda - Esta mensagem\n\n"
            "*Como comprar:*\n"
            "1. Use /produtos para ver os produtos\n"
            "2. Clique em 'Comprar' no produto desejado\n"
            "3. Escolha a forma de pagamento\n"
            "4. Realize o pagamento\n"
            "5. Receba o link de acesso automaticamente\n\n"
            "*Precisa de ajuda?*\n"
            "Entre em contato: @suporte"
        )
        
        if update.callback_query:
            await update.callback_query.message.reply_text(help_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        text = update.message.text.lower()
        
        if "produto" in text or "comprar" in text:
            await self.products_command(update, context)
        elif "pedido" in text:
            await self.orders_command(update, context)
        elif "ajuda" in text or "help" in text:
            await self.help_command(update, context)
        else:
            await update.message.reply_text(
                "Não entendi sua mensagem. 🤔\n"
                "Use /ajuda para ver os comandos disponíveis."
            )
    
    async def cancel_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
        """Cancel an order"""
        # Cancel order in database
        
        await update.callback_query.message.reply_text(
            "❌ Pedido cancelado com sucesso!",
            parse_mode='Markdown'
        )
