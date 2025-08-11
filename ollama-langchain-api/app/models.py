from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """Modelo para requisições de chat simples"""
    message: str = Field(..., description="Mensagem do usuário", min_length=1, max_length=2000)
    temperature: Optional[float] = Field(0.7, description="Temperatura para geração", ge=0.0, le=2.0)


class ChatWithContextRequest(BaseModel):
    """Modelo para requisições de chat com contexto"""
    message: str = Field(..., description="Mensagem do usuário", min_length=1, max_length=2000)
    context: str = Field(..., description="Contexto adicional para o modelo", min_length=1, max_length=5000)
    temperature: Optional[float] = Field(0.7, description="Temperatura para geração", ge=0.0, le=2.0)


class ChatWithMemoryRequest(BaseModel):
    """Modelo para requisições de chat com memória"""
    message: str = Field(..., description="Mensagem do usuário", min_length=1, max_length=2000)
    session_id: str = Field(..., description="ID da sessão para manter memória", min_length=1, max_length=100)
    temperature: Optional[float] = Field(0.7, description="Temperatura para geração", ge=0.0, le=2.0)


class ChainRequest(BaseModel):
    """Modelo para requisições usando LangChain chains"""
    message: str = Field(..., description="Mensagem do usuário", min_length=1, max_length=2000)
    chain_type: str = Field(..., description="Tipo de chain a ser usado", pattern="^(simple|qa|summarize|translate)$")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parâmetros adicionais para a chain")


class ChatResponse(BaseModel):
    """Modelo para respostas de chat"""
    response: str = Field(..., description="Resposta do modelo")
    model_used: str = Field(..., description="Modelo utilizado")
    tokens_used: Optional[int] = Field(None, description="Número de tokens utilizados")
    processing_time: Optional[float] = Field(None, description="Tempo de processamento em segundos")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")


class HealthResponse(BaseModel):
    """Modelo para resposta de health check"""
    status: str = Field(..., description="Status da API")
    ollama_status: str = Field(..., description="Status da conexão com Ollama")
    model_loaded: str = Field(..., description="Modelo carregado")
    timestamp: str = Field(..., description="Timestamp da verificação")
