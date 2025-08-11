import logging
import sys
from pathlib import Path
from datetime import datetime
import os

class ColoredFormatter(logging.Formatter):
    """Formatter personalizado com cores para diferentes níveis de log"""
    
    # Cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Adicionar cor ao nível do log
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Adicionar cor à mensagem para ERROR e CRITICAL
        if levelname in ['ERROR', 'CRITICAL']:
            record.msg = f"{self.COLORS[levelname]}{record.msg}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logger(name: str = "ollama-langchain-api", level: str = "INFO") -> logging.Logger:
    """
    Configura e retorna um logger personalizado
    
    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    
    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Criar diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Formatter para console (com cores)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formatter para arquivo (sem cores)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Handler para arquivo de log geral
    today = datetime.now().strftime('%Y-%m-%d')
    general_log_file = log_dir / f"app_{today}.log"
    file_handler = logging.FileHandler(general_log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Handler para arquivo de erros
    error_log_file = log_dir / f"errors_{today}.log"
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Handler para arquivo de requisições da API
    api_log_file = log_dir / f"api_{today}.log"
    api_handler = logging.FileHandler(api_log_file, encoding='utf-8')
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(file_formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    # Criar logger específico para API
    api_logger = logging.getLogger(f"{name}.api")
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    
    return logger

def get_api_logger() -> logging.Logger:
    """Retorna o logger específico para logs da API"""
    return logging.getLogger("ollama-langchain-api.api")

def log_request(logger: logging.Logger, method: str, url: str, status_code: int, 
                processing_time: float, user_agent: str = None, ip: str = None):
    """
    Log estruturado para requisições HTTP
    
    Args:
        logger: Logger instance
        method: Método HTTP (GET, POST, etc.)
        url: URL da requisição
        status_code: Código de status da resposta
        processing_time: Tempo de processamento em segundos
        user_agent: User-Agent do cliente (opcional)
        ip: IP do cliente (opcional)
    """
    
    # Determinar nível baseado no status code
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO
    
    # Construir mensagem estruturada
    message = f"HTTP {method} {url} - Status: {status_code} - Time: {processing_time:.3f}s"
    
    if user_agent:
        message += f" - UA: {user_agent}"
    if ip:
        message += f" - IP: {ip}"
    
    logger.log(level, message)

def log_chat_request(logger: logging.Logger, endpoint: str, message_length: int, 
                    model: str, temperature: float = None, session_id: str = None):
    """
    Log estruturado para requisições de chat
    
    Args:
        logger: Logger instance
        endpoint: Endpoint da API (/chat, /chat/context, etc.)
        message_length: Tamanho da mensagem
        model: Modelo usado
        temperature: Temperatura (opcional)
        session_id: ID da sessão (opcional)
    """
    
    message = f"Chat Request - Endpoint: {endpoint} - Model: {model} - Msg Length: {message_length}"
    
    if temperature is not None:
        message += f" - Temp: {temperature}"
    if session_id:
        message += f" - Session: {session_id}"
    
    logger.info(message)

def log_chat_response(logger: logging.Logger, response_length: int, processing_time: float, 
                     model: str, tokens_used: int = None):
    """
    Log estruturado para respostas de chat
    
    Args:
        logger: Logger instance
        response_length: Tamanho da resposta
        processing_time: Tempo de processamento
        model: Modelo usado
        tokens_used: Tokens utilizados (opcional)
    """
    
    message = f"Chat Response - Model: {model} - Response Length: {response_length} - Time: {processing_time:.3f}s"
    
    if tokens_used:
        message += f" - Tokens: {tokens_used}"
    
    logger.info(message)

def log_error(logger: logging.Logger, error: Exception, context: str = None, 
              request_info: dict = None):
    """
    Log estruturado para erros
    
    Args:
        logger: Logger instance
        error: Exceção capturada
        context: Contexto onde o erro ocorreu
        request_info: Informações da requisição (opcional)
    """
    
    message = f"Error in {context or 'unknown context'}: {type(error).__name__}: {str(error)}"
    
    if request_info:
        message += f" - Request: {request_info}"
    
    logger.error(message, exc_info=True)

# Configurar logger principal
main_logger = setup_logger()
api_logger = get_api_logger()
