import asyncio
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.services.order_service import OrderService
from app.services.access_service import AccessService
from app.services.message_service import MessageService
from app.services.telegram_service import TelegramService
from app.models.order import OrderStatus


async def check_pending_payments():
    """Check for pending payments and send reminders"""
    try:
        async for session in get_async_session():
            order_service = OrderService(session)
            message_service = MessageService(session)
            
            # Get orders pending for more than 1 hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            three_hours_ago = datetime.utcnow() - timedelta(hours=3)
            six_hours_ago = datetime.utcnow() - timedelta(hours=6)
            
            orders = await order_service.get_orders(status="pending")
            
            for order in orders:
                reminder_sent = False
                
                # Send reminders based on time elapsed
                if order.created_at < six_hours_ago:
                    # Third reminder
                    message = await message_service.render_reminder(order.user, order, 3)
                    reminder_sent = True
                elif order.created_at < three_hours_ago:
                    # Second reminder
                    message = await message_service.render_reminder(order.user, order, 2)
                    reminder_sent = True
                elif order.created_at < one_hour_ago:
                    # First reminder
                    message = await message_service.render_reminder(order.user, order, 1)
                    reminder_sent = True
                
                if reminder_sent:
                    from app.main import telegram_service
                    await telegram_service.send_reminder(order.user.telegram_id, message)
                    logger.info(f"Sent payment reminder for order {order.order_number}")
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Error checking pending payments: {e}")


async def check_expired_orders():
    """Cancel expired orders"""
    try:
        async for session in get_async_session():
            order_service = OrderService(session)
            
            # Get orders older than 24 hours
            expired_orders = await order_service.get_expired_orders(hours=24)
            
            for order in expired_orders:
                await order_service.update_order_status(order.id, OrderStatus.EXPIRED)
                logger.info(f"Expired order {order.order_number}")
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Error checking expired orders: {e}")


async def check_expiring_accesses():
    """Check for expiring accesses and notify users"""
    try:
        async for session in get_async_session():
            access_service = AccessService(session)
            message_service = MessageService(session)
            
            # Check accesses expiring in 24 hours
            expiring_accesses = await access_service.get_expiring_accesses(hours=24)
            
            for access in expiring_accesses:
                # Send expiry notification
                template = await message_service.get_template_by_type(
                    "access_expiring",
                    access.user.language_code
                )
                
                if template:
                    message = template.render(
                        user_name=access.user.full_name,
                        expires_at=access.expires_at.strftime("%d/%m/%Y %H:%M")
                    )
                    
                    from app.main import telegram_service
                    await telegram_service.send_reminder(access.user.telegram_id, message)
                    logger.info(f"Sent expiry notification for access {access.id}")
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Error checking expiring accesses: {e}")


async def remove_expired_accesses():
    """Remove users from groups when access expires"""
    try:
        async for session in get_async_session():
            access_service = AccessService(session)
            
            # Get expired accesses
            expired_accesses = await access_service.get_expired_accesses()
            
            for access in expired_accesses:
                # Remove user from Telegram group
                from app.main import telegram_service
                removed = await telegram_service.remove_user_from_group(
                    access.user.telegram_id,
                    access.telegram_group_id
                )
                
                if removed:
                    # Revoke access
                    await access_service.revoke_access(access.id, "Access expired")
                    logger.info(f"Removed user {access.user.telegram_id} from group {access.telegram_group_id}")
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Error removing expired accesses: {e}")


async def scheduler_loop():
    """Main scheduler loop"""
    logger.info("Starting scheduler...")
    
    while True:
        try:
            # Run tasks
            await check_pending_payments()
            await check_expired_orders()
            await check_expiring_accesses()
            await remove_expired_accesses()
            
            # Wait 30 minutes before next run
            await asyncio.sleep(1800)
            
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error


async def start_scheduler():
    """Start the scheduler"""
    asyncio.create_task(scheduler_loop())
