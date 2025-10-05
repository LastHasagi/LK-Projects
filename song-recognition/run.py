#!/usr/bin/env python3
"""
Script para executar a aplicação Song Recognition
"""
import os
import sys
from app import app

if __name__ == '__main__':
    # Configurações para desenvolvimento
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print("🎵 Iniciando Song Recognition...")
    print(f"📍 Servidor rodando em: http://{host}:{port}")
    print(f"🐛 Modo debug: {'Ativado' if debug_mode else 'Desativado'}")
    print("=" * 50)
    
    try:
        app.run(
            debug=debug_mode,
            host=host,
            port=port,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Aplicação encerrada pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {str(e)}")
        sys.exit(1)
