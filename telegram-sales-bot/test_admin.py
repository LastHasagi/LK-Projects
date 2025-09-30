#!/usr/bin/env python
"""
Script minimalista para testar apenas o painel admin
Sem bot do Telegram, sem pagamentos - apenas o admin
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent))

# Criar .env mínimo se não existir
if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write("""TELEGRAM_BOT_TOKEN=fake_token_for_testing
DATABASE_URL=sqlite:///./test_admin.db
SECRET_KEY=test-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
DEBUG=True
""")
    print("✅ Arquivo .env criado para teste")

# Criar diretórios
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('logs', exist_ok=True)

print("\n🚀 Iniciando Painel Admin (Modo Teste)")
print("=" * 40)
print("URL: http://localhost:8000/admin")
print("Usuário: admin")
print("Senha: admin123")
print("=" * 40)
print("\nInstalando dependências mínimas...")

# Instalar apenas o essencial
os.system("pip install fastapi uvicorn sqlalchemy aiosqlite jinja2 python-multipart")

print("\nIniciando servidor...\n")

# Código mínimo para rodar o admin
code = '''
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return RedirectResponse(url="/admin")

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Painel Admin - Bot de Vendas</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">🤖 Bot de Vendas - Admin</a>
            </div>
        </nav>
        
        <div class="container mt-5">
            <h1>Painel Administrativo</h1>
            <p class="lead">Bem-vindo ao painel de controle do Bot de Vendas!</p>
            
            <div class="row mt-4">
                <div class="col-md-3">
                    <div class="card text-white bg-primary mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Produtos</h5>
                            <p class="card-text">0 produtos cadastrados</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-success mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Vendas</h5>
                            <p class="card-text">R$ 0,00</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-warning mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Pedidos</h5>
                            <p class="card-text">0 pedidos</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-info mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Usuários</h5>
                            <p class="card-text">0 usuários</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="alert alert-info mt-4">
                <h4>🎉 Painel Admin Funcionando!</h4>
                <p>Este é um modo de demonstração. Para funcionalidade completa:</p>
                <ol>
                    <li>Configure o token do bot no arquivo .env</li>
                    <li>Instale todas as dependências: <code>pip install -r requirements.txt</code></li>
                    <li>Execute: <code>python -m app.main</code></li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
'''

# Executar
exec(code)
