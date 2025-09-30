from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import asyncio
from loguru import logger

from app.config import get_settings
from app.database import init_db, close_db
from app.routers import admin, api, webhook, auth
from app.services.telegram_service import TelegramService
from app.utils.scheduler import start_scheduler

settings = get_settings()

# Global telegram service instance
telegram_service = TelegramService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting application...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Telegram bot
    await telegram_service.initialize()
    logger.info("Telegram bot initialized")
    
    # Start background tasks
    scheduler_task = asyncio.create_task(start_scheduler())
    
    # Start telegram bot polling in development
    if settings.debug and not settings.telegram_webhook_url:
        asyncio.create_task(telegram_service.app.run_polling())
        logger.info("Telegram bot polling started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Cancel background tasks
    scheduler_task.cancel()
    
    # Close database connections
    await close_db()
    
    # Stop telegram bot
    if telegram_service.app:
        await telegram_service.app.stop()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.upload_folder), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])


@app.get("/")
async def root():
    """Redirect to admin panel"""
    return RedirectResponse(url="/admin")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
