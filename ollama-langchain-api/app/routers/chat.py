from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import time

from ..models import (
    ChatRequest, 
    ChatWithContextRequest, 
    ChatWithMemoryRequest, 
    ChainRequest,
    ChatResponse,
    HealthResponse
)
from ..services.ollama_service import OllamaService
from ..services.langchain_service import LangChainService
from ..utils.logger import api_logger, log_chat_request, log_chat_response, log_error

logger = api_logger

router = APIRouter(prefix="/chat", tags=["chat"])

# Instâncias dos serviços
ollama_service = OllamaService()
langchain_service = LangChainService()


@router.post("/simple", response_model=ChatResponse, summary="Chat simples")
async def simple_chat(request: ChatRequest):
    """
    Endpoint para chat simples com o modelo Ollama.
    
    - **message**: Mensagem do usuário
    - **temperature**: Temperatura para geração (opcional, padrão: 0.7)
    """
    start_time = time.time()
    
    try:
        # Log da requisição
        log_chat_request(
            logger=logger,
            endpoint="/chat/simple",
            message_length=len(request.message),
            model=ollama_service.model_name,
            temperature=request.temperature
        )
        
        result = ollama_service.generate_response(
            message=request.message,
            temperature=request.temperature
        )
        
        # Log da resposta
        log_chat_response(
            logger=logger,
            response_length=len(result["response"]),
            processing_time=result["processing_time"],
            model=result["model_used"],
            tokens_used=result.get("tokens_used")
        )
        
        return ChatResponse(
            response=result["response"],
            model_used=result["model_used"],
            processing_time=result["processing_time"],
            metadata={
                "temperature": result["temperature"],
                "endpoint": "simple"
            }
        )
    except Exception as e:
        log_error(
            logger=logger,
            error=e,
            context="simple_chat",
            request_info={
                "message_length": len(request.message),
                "temperature": request.temperature
            }
        )
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/with-context", response_model=ChatResponse, summary="Chat com contexto")
async def chat_with_context(request: ChatWithContextRequest):
    """
    Endpoint para chat com contexto adicional.
    
    - **message**: Mensagem do usuário
    - **context**: Contexto adicional para o modelo
    - **temperature**: Temperatura para geração (opcional, padrão: 0.7)
    """
    try:
        result = ollama_service.generate_with_context(
            message=request.message,
            context=request.context,
            temperature=request.temperature
        )
        
        return ChatResponse(
            response=result["response"],
            model_used=result["model_used"],
            processing_time=result["processing_time"],
            metadata={
                "temperature": result["temperature"],
                "context_used": result["context_used"],
                "endpoint": "with-context"
            }
        )
    except Exception as e:
        logger.error(f"Erro no chat com contexto: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/with-memory", response_model=ChatResponse, summary="Chat com memória")
async def chat_with_memory(request: ChatWithMemoryRequest):
    """
    Endpoint para chat com memória de conversas.
    
    - **message**: Mensagem do usuário
    - **session_id**: ID da sessão para manter memória
    - **temperature**: Temperatura para geração (opcional, padrão: 0.7)
    """
    try:
        result = langchain_service.chat_with_memory(
            message=request.message,
            session_id=request.session_id,
            temperature=request.temperature
        )
        
        return ChatResponse(
            response=result["response"],
            model_used=result["model_used"],
            processing_time=result["processing_time"],
            metadata={
                "session_id": result["session_id"],
                "memory_used": result["memory_used"],
                "conversation_history_length": len(result["conversation_history"]),
                "endpoint": "with-memory"
            }
        )
    except Exception as e:
        logger.error(f"Erro no chat com memória: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/chain", response_model=ChatResponse, summary="Chat usando LangChain chains")
async def chat_with_chain(request: ChainRequest):
    """
    Endpoint para chat usando diferentes tipos de LangChain chains.
    
    - **message**: Mensagem do usuário
    - **chain_type**: Tipo de chain (simple, qa, summarize, translate)
    - **parameters**: Parâmetros adicionais para a chain
    """
    try:
        chain_type = request.chain_type
        parameters = request.parameters or {}
        
        if chain_type == "simple":
            result = ollama_service.generate_response(
                message=request.message,
                temperature=parameters.get("temperature", 0.7)
            )
        elif chain_type == "qa":
            if "context" not in parameters:
                raise HTTPException(status_code=400, detail="Contexto é obrigatório para QA chain")
            result = langchain_service.qa_chain(
                question=request.message,
                context=parameters["context"],
                temperature=parameters.get("temperature", 0.7)
            )
        elif chain_type == "summarize":
            result = langchain_service.summarize_chain(
                text=request.message,
                max_length=parameters.get("max_length", 200),
                temperature=parameters.get("temperature", 0.7)
            )
        elif chain_type == "translate":
            if "target_language" not in parameters:
                raise HTTPException(status_code=400, detail="target_language é obrigatório para translate chain")
            result = langchain_service.translate_chain(
                text=request.message,
                target_language=parameters["target_language"],
                temperature=parameters.get("temperature", 0.7)
            )
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de chain '{chain_type}' não suportado")
        
        return ChatResponse(
            response=result["response"],
            model_used=result["model_used"],
            processing_time=result["processing_time"],
            metadata={
                "chain_type": result.get("chain_type", "simple"),
                "temperature": parameters.get("temperature", 0.7),
                "endpoint": "chain"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no chat com chain: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/code-analysis", response_model=ChatResponse, summary="Análise de código")
async def code_analysis(request: ChatWithContextRequest):
    """
    Endpoint para análise de código usando LangChain.
    
    - **message**: Pergunta sobre o código
    - **context**: Código a ser analisado
    - **temperature**: Temperatura para geração (opcional, padrão: 0.7)
    """
    try:
        result = langchain_service.code_analysis_chain(
            code=request.context,
            analysis_type=request.message,
            temperature=request.temperature
        )
        
        return ChatResponse(
            response=result["response"],
            model_used=result["model_used"],
            processing_time=result["processing_time"],
            metadata={
                "chain_type": result["chain_type"],
                "analysis_type": result["analysis_type"],
                "temperature": request.temperature,
                "endpoint": "code-analysis"
            }
        )
    except Exception as e:
        logger.error(f"Erro na análise de código: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/memory/{session_id}", summary="Obter informações da memória")
async def get_memory_info(session_id: str):
    """
    Endpoint para obter informações sobre a memória de uma sessão.
    
    - **session_id**: ID da sessão
    """
    try:
        result = langchain_service.get_memory_info(session_id)
        return result
    except Exception as e:
        logger.error(f"Erro ao obter informações da memória: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.delete("/memory/{session_id}", summary="Limpar memória da sessão")
async def clear_memory(session_id: str):
    """
    Endpoint para limpar a memória de uma sessão.
    
    - **session_id**: ID da sessão
    """
    try:
        success = langchain_service.clear_memory(session_id)
        if success:
            return {"message": f"Memória da sessão {session_id} foi limpa com sucesso"}
        else:
            return {"message": f"Sessão {session_id} não encontrada"}
    except Exception as e:
        logger.error(f"Erro ao limpar memória: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/models", summary="Listar modelos disponíveis")
async def list_models():
    """
    Endpoint para listar todos os modelos disponíveis no Ollama.
    """
    try:
        result = ollama_service.list_models()
        return result
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """
    Endpoint para verificar a saúde da API e conexão com Ollama.
    """
    try:
        import datetime
        
        ollama_health = ollama_service.check_health()
        
        return HealthResponse(
            status="healthy" if ollama_health["status"] == "healthy" else "unhealthy",
            ollama_status=ollama_health["status"],
            model_loaded=ollama_health.get("current_model", "unknown"),
            timestamp=datetime.datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
