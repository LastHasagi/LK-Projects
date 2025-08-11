import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import time

from .routers import chat
from .utils.logger import main_logger, api_logger, log_request, log_error

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logger
logger = main_logger

# Criar aplicação FastAPI
app = FastAPI(
    title="🚀 Ollama + LangChain API",
    description="""
    ## API para demonstrar integração entre Ollama e LangChain
    
    Esta API mostra como turbinar modelos de IA locais usando LangChain para criar aplicações mais inteligentes e contextuais.
    
    ### Funcionalidades:
    - ✅ Chat simples com modelos Ollama
    - ✅ Chat com contexto adicional
    - ✅ Chat com memória de conversas
    - ✅ Diferentes tipos de LangChain chains
    - ✅ Análise de código
    - ✅ Health check e monitoramento
    
    ### Tecnologias:
    - **FastAPI**: Framework web moderno
    - **Ollama**: Para rodar modelos localmente
    - **LangChain**: Framework para aplicações de IA
    - **Pydantic**: Validação de dados
    
    ### Como usar:
    1. Instale o Ollama: https://ollama.ai/
    2. Baixe um modelo: `ollama pull llama2`
    3. Configure as variáveis de ambiente
    4. Execute: `uvicorn app.main:app --reload`
    5. Acesse: http://localhost:8000/docs
    """,
    version="1.0.0",
    contact={
        "name": "Desenvolvedor",
        "url": "https://github.com/LastHasagi?tab=repositories",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        # Processar requisição
        response = await call_next(request)
        
        # Calcular tempo de processamento
        process_time = time.time() - start_time
        
        # Log estruturado da requisição
        log_request(
            logger=api_logger,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            processing_time=process_time,
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host if request.client else None
        )
        
        # Adicionar header com tempo de processamento
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # Log de erro se algo der errado
        process_time = time.time() - start_time
        log_error(
            logger=logger,
            error=e,
            context="request_middleware",
            request_info={
                "method": request.method,
                "url": str(request.url),
                "processing_time": process_time
            }
        )
        raise


# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_error(
        logger=logger,
        error=exc,
        context="global_exception_handler",
        request_info={
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers)
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


# Configurar arquivos estáticos
try:
    app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")
    logger.info("✅ Arquivos estáticos montados com sucesso")
except Exception as e:
    logger.warning(f"⚠️ Não foi possível montar arquivos estáticos: {e}")

# Incluir routers
app.include_router(chat.router)


# Endpoint raiz - serve o frontend
@app.get("/", summary="Página inicial")
async def root():
    """
    Endpoint raiz da API.
    
    Serve o frontend da aplicação.
    """
    try:
        return FileResponse("static/index.html")
    except FileNotFoundError:
        # Fallback para JSON se o frontend não estiver disponível
        return {
            "message": "🚀 Ollama + LangChain API",
            "description": "API para demonstrar integração entre Ollama e LangChain",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "frontend": "Frontend não encontrado. Acesse /docs para a documentação da API.",
            "endpoints": {
                "chat_simple": "/chat",
                "chat_with_context": "/chat/context",
                "chat_with_memory": "/chat/memory",
                "chat_chain": "/chat/chain",
                "models": "/chat/models",
                "health": "/health"
            },
            "technologies": [
                "FastAPI",
                "Ollama",
                "LangChain",
                "Pydantic"
            ]
        }


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    logger.info("🚀 Iniciando Ollama + LangChain API...")
    logger.info(f"Modelo configurado: {os.getenv('OLLAMA_MODEL', 'llama2')}")
    logger.info(f"URL do Ollama: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    logger.info("🛑 Encerrando Ollama + LangChain API...")


# Health check simples
@app.get("/health", summary="Health check simples")
async def simple_health():
    """
    Health check simples da API.
    
    Para health check completo com Ollama, use: /chat/health
    """
    return {
        "status": "healthy",
        "service": "ollama-langchain-api",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Configurações para execução direta
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Iniciando servidor em {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
