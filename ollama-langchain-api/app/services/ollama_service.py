import os
import time
import requests
from typing import Dict, Any, Optional
from langchain_community.llms import Ollama
from langchain.schema import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)


class OllamaService:
    """Serviço para integração com Ollama"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama2")
        self.ollama = None
        self._initialize_ollama()
    
    def _initialize_ollama(self):
        """Inicializa a conexão com o Ollama"""
        try:
            self.ollama = Ollama(
                base_url=self.base_url,
                model=self.model_name,
                temperature=0.7
            )
            logger.info(f"Ollama inicializado com modelo: {self.model_name}")
        except Exception as e:
            logger.error(f"Erro ao inicializar Ollama: {e}")
            raise
    
    def check_health(self) -> Dict[str, Any]:
        """Verifica a saúde da conexão com Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                return {
                    "status": "healthy",
                    "models_available": model_names,
                    "current_model": self.model_name,
                    "base_url": self.base_url
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "base_url": self.base_url
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "base_url": self.base_url
            }
    
    def generate_response(self, message: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Gera uma resposta simples do modelo"""
        start_time = time.time()
        
        try:
            response = self.ollama.invoke(message)
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "model_used": self.model_name,
                "processing_time": round(processing_time, 3),
                "temperature": temperature
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            raise
    
    def generate_with_context(self, message: str, context: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Gera resposta com contexto adicional"""
        start_time = time.time()
        
        try:
            # Criar prompt com contexto
            prompt = f"""Contexto: {context}

Pergunta: {message}

Por favor, responda baseado no contexto fornecido:"""
            
            response = self.ollama.invoke(prompt)
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "model_used": self.model_name,
                "processing_time": round(processing_time, 3),
                "temperature": temperature,
                "context_used": True
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com contexto: {e}")
            raise
    
    def list_models(self) -> Dict[str, Any]:
        """Lista todos os modelos disponíveis no Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def change_model(self, model_name: str) -> bool:
        """Altera o modelo ativo"""
        try:
            # Verificar se o modelo existe
            models_response = self.list_models()
            if "models" in models_response:
                available_models = [model["name"] for model in models_response["models"]]
                if model_name in available_models:
                    self.model_name = model_name
                    self._initialize_ollama()
                    return True
                else:
                    logger.error(f"Modelo {model_name} não encontrado")
                    return False
            else:
                logger.error("Não foi possível listar modelos")
                return False
        except Exception as e:
            logger.error(f"Erro ao alterar modelo: {e}")
            return False
