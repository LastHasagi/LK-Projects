#!/usr/bin/env python
"""
Script de configuração inicial do Bot de Vendas Telegram
"""
import os
import sys
import secrets
import asyncio
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent))


def generate_secret_key():
    """Gera uma chave secreta segura"""
    return secrets.token_urlsafe(32)


def create_env_file():
    """Cria arquivo .env se não existir"""
    if os.path.exists('.env'):
        print("✓ Arquivo .env já existe")
        return
    
    print("Criando arquivo .env...")
    
    # Copia do exemplo
    with open('env.example', 'r') as f:
        content = f.read()
    
    # Gera secret key
    secret_key = generate_secret_key()
    content = content.replace('your-secret-key-here-generate-with-openssl-rand-hex-32', secret_key)
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print("✓ Arquivo .env criado com sucesso!")
    print("⚠️  IMPORTANTE: Edite o arquivo .env com suas configurações antes de iniciar o bot")


def create_directories():
    """Cria diretórios necessários"""
    dirs = [
        'static/uploads',
        'logs',
        'migrations/versions'
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    print("✓ Diretórios criados")


async def initialize_database():
    """Inicializa o banco de dados"""
    try:
        # Import here to avoid loading config before .env exists
        from app.database import init_db_sync
        from app.database import get_sync_session
        from app.services.message_service import MessageService
        
        print("Inicializando banco de dados...")
        init_db_sync()
        print("✓ Banco de dados inicializado")
        
        # Cria templates padrão
        with get_sync_session() as db:
            service = MessageService(db)
            await service.initialize_default_templates()
        
        print("✓ Templates de mensagens criados")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        print("Verifique as configurações de DATABASE_URL no arquivo .env")
        sys.exit(1)


def print_instructions():
    """Imprime instruções de configuração"""
    print("\n" + "="*50)
    print("CONFIGURAÇÃO INICIAL COMPLETA!")
    print("="*50)
    print("\nPróximos passos:")
    print("\n1. Configure o arquivo .env com:")
    print("   - Token do bot do Telegram (obtenha com @BotFather)")
    print("   - Credenciais do Mercado Pago")
    print("   - URL do banco de dados PostgreSQL")
    print("   - Senha do admin")
    print("\n2. Execute as migrações do banco:")
    print("   alembic upgrade head")
    print("\n3. Inicie o servidor:")
    print("   python -m app.main")
    print("\n4. Acesse o painel admin:")
    print("   http://localhost:8000/admin")
    print("\n5. Configure no Telegram:")
    print("   - Adicione comandos do bot com @BotFather")
    print("   - Configure webhook se necessário")
    print("\n" + "="*50)


def main():
    """Função principal"""
    print("Bot de Vendas Telegram - Setup Inicial")
    print("="*50)
    
    # Verifica Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 ou superior é necessário")
        sys.exit(1)
    
    print(f"✓ Python {sys.version.split()[0]}")
    
    # Cria arquivo .env
    create_env_file()
    
    # Cria diretórios
    create_directories()
    
    # Pergunta se deve inicializar o banco
    response = input("\nDeseja inicializar o banco de dados agora? (s/n): ").lower()
    if response == 's':
        try:
            # Import here to check if .env is configured
            from app.config import get_settings
            settings = get_settings()
            asyncio.run(initialize_database())
        except Exception as e:
            print(f"❌ Erro: {e}")
            print("Configure o arquivo .env primeiro")
    
    # Imprime instruções
    print_instructions()


if __name__ == "__main__":
    main()
