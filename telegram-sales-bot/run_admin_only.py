"""
Script para executar APENAS o painel admin (sem bot do Telegram)
Perfeito para desenvolvimento e testes no Windows
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent))

def main():
    print("=== Painel Admin - Bot de Vendas ===\n")
    
    # Força o uso de SQLite criando um .env temporário
    print("🔧 Configurando ambiente para SQLite...")
    
    # Salva o .env original se existir
    env_backup = None
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            env_backup = f.read()
    
    # Cria .env para SQLite
    with open('.env', 'w', encoding='utf-8') as f:
        f.write("""# Bot Configuration - LOCAL/DEV
TELEGRAM_BOT_TOKEN=fake_token_for_testing
TELEGRAM_WEBHOOK_URL=

# Database - SQLite (não precisa instalar nada!)
DATABASE_URL=sqlite:///./telegram_sales_bot.db
REDIS_URL=

# Security
SECRET_KEY=dev-secret-key-only-for-testing
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Payment Gateways (deixe vazio para testes)
MERCADOPAGO_ACCESS_TOKEN=
MERCADOPAGO_PUBLIC_KEY=
MERCADOPAGO_WEBHOOK_SECRET=

# Application
APP_NAME="Telegram Sales Bot"
APP_VERSION="1.0.0"
DEBUG=True
HOST=127.0.0.1
PORT=8000

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Telegram Groups
DEFAULT_INVITE_LINK_EXPIRY_HOURS=24
""")
    
    print("✅ Configuração SQLite criada")
    
    # Cria diretórios necessários
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    print("✅ Diretórios criados")
    
    # Inicializa o banco SQLite
    print("\n🔄 Inicializando banco de dados SQLite...")
    try:
        from app.database import init_db_sync
        init_db_sync()
        print("✅ Banco de dados criado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        return
    
    # Cria um app simplificado sem o bot do Telegram
    print("\n🚀 Iniciando servidor (APENAS PAINEL ADMIN)...")
    print("📌 Painel Admin: http://localhost:8000/admin")
    print("👤 Usuário: admin")
    print("🔑 Senha: admin123")
    print("\n⚠️  Bot do Telegram DESATIVADO neste modo")
    print("[Pressione Ctrl+C para parar]\n")
    
    try:
        # Cria um arquivo temporário com app simplificado
        app_content = '''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db, close_db
from app.routers import admin, api, webhook, auth

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()

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
    return RedirectResponse(url="/admin")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "mode": "admin_only"
    }
'''
        
        # Salva temporariamente
        with open('app_admin_only.py', 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        import uvicorn
        uvicorn.run(
            "app_admin_only:app",
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✋ Servidor parado")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    finally:
        # Remove arquivo temporário
        if os.path.exists('app_admin_only.py'):
            os.remove('app_admin_only.py')
        
        # Restaura o .env original se existia
        if env_backup:
            print("\n🔄 Restaurando configuração original...")
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_backup)
            print("✅ Configuração original restaurada")

if __name__ == "__main__":
    main()


