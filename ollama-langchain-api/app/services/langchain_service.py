import os
import time
from typing import Dict, Any, List, Optional
from langchain_community.llms import Ollama
from langchain.chains import LLMChain, ConversationChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.schema import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)


class LangChainService:
    """Serviço para funcionalidades avançadas do LangChain"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama2")
        self.ollama = None
        self.memories = {}  # Armazena memórias por sessão
        self._initialize_ollama()
    
    def _initialize_ollama(self):
        """Inicializa a conexão com o Ollama"""
        try:
            self.ollama = Ollama(
                base_url=self.base_url,
                model=self.model_name,
                temperature=0.7
            )
            logger.info(f"LangChain Ollama inicializado com modelo: {self.model_name}")
        except Exception as e:
            logger.error(f"Erro ao inicializar LangChain Ollama: {e}")
            raise
    
    def get_memory(self, session_id: str) -> ConversationBufferMemory:
        """Obtém ou cria uma memória para a sessão"""
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferMemory(
                memory_key="history",
                return_messages=True
            )
        return self.memories[session_id]
    
    def chat_with_memory(self, message: str, session_id: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Chat com memória de conversas"""
        start_time = time.time()
        
        try:
            memory = self.get_memory(session_id)
            
            # Criar chain com memória
            conversation = ConversationChain(
                llm=self.ollama,
                memory=memory,
                verbose=False
            )
            
            response = conversation.predict(input=message)
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "model_used": self.model_name,
                "processing_time": round(processing_time, 3),
                "session_id": session_id,
                "memory_used": True,
                "conversation_history": memory.chat_memory.messages
            }
        except Exception as e:
            logger.error(f"Erro no chat com memória: {e}")
            raise
    
    def qa_chain(self, question: str, context: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Chain para perguntas e respostas com contexto"""
        start_time = time.time()
        
        try:
            # Template para QA
            qa_template = """Você é um assistente especializado em responder perguntas baseado no contexto fornecido.

Contexto: {context}

Pergunta: {question}

Resposta baseada no contexto:"""
            
            prompt = PromptTemplate(
                input_variables=["context", "question"],
                template=qa_template
            )
            
            qa_chain = LLMChain(
                llm=self.ollama,
                prompt=prompt
            )
            
            response = qa_chain.run(context=context, question=question)
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "model_used": self.model_name,
                "processing_time": round(processing_time, 3),
                "chain_type": "qa",
                "context_used": True
            }
        except Exception as e:
            logger.error(f"Erro na QA chain: {e}")
            raise
    
    def summarize_chain(self, text: str, max_length: int = 200, temperature: float = 0.7) -> Dict[str, Any]:
        """Chain para sumarização de texto"""
        start_time = time.time()
        
        try:
            # Template para sumarização
            summarize_template = """Você é um especialista em sumarização de texto.

Texto para sumarizar: {text}

Crie um resumo conciso com no máximo {max_length} palavras, mantendo os pontos principais:"""
            
            prompt = PromptTemplate(
                input_variables=["text", "max_length"],
                template=summarize_template
            )
            
            summarize_chain = LLMChain(
                llm=self.ollama,
                prompt=prompt
            )
            
            response = summarize_chain.run(text=text, max_length=max_length)
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "model_used": self.model_name,
                "processing_time": round(processing_time, 3),
                "chain_type": "summarize",
                "max_length": max_length
            }
        except Exception as e:
            logger.error(f"Erro na summarize chain: {e}")
            raise
    
    def translate_chain(self, text: str, target_language: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Chain para tradução de texto"""
        start_time = time.time()
        
        try:
            # Template para tradução
            translate_template = """Você é um tradutor profissional.

Traduza o seguinte texto para {target_language}:

Texto: {text}

Tradução:"""
            
            prompt = PromptTemplate(
                input_variables=["text", "target_language"],
                template=translate_template
            )
            
            translate_chain = LLMChain(
                llm=self.ollama,
                prompt=prompt
            )
            
            response = translate_chain.run(text=text, target_language=target_language)
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "model_used": self.model_name,
                "processing_time": round(processing_time, 3),
                "chain_type": "translate",
                "target_language": target_language
            }
        except Exception as e:
            logger.error(f"Erro na translate chain: {e}")
            raise
    
    def code_analysis_chain(self, code: str, analysis_type: str = "general", temperature: float = 0.7) -> Dict[str, Any]:
        """Chain para análise de código"""
        start_time = time.time()
        
        try:
            # Template para análise de código
            code_template = """Você é um especialista em análise de código.

Código para analisar:
{code}

Tipo de análise: {analysis_type}

Por favor, forneça uma análise detalhada do código, incluindo:
- Estrutura e organização
- Boas práticas
- Possíveis melhorias
- Problemas potenciais
- Sugestões de otimização

Análise:"""
            
            prompt = PromptTemplate(
                input_variables=["code", "analysis_type"],
                template=code_template
            )
            
            code_chain = LLMChain(
                llm=self.ollama,
                prompt=prompt
            )
            
            response = code_chain.run(code=code, analysis_type=analysis_type)
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "model_used": self.model_name,
                "processing_time": round(processing_time, 3),
                "chain_type": "code_analysis",
                "analysis_type": analysis_type
            }
        except Exception as e:
            logger.error(f"Erro na code analysis chain: {e}")
            raise
    
    def clear_memory(self, session_id: str) -> bool:
        """Limpa a memória de uma sessão específica"""
        try:
            if session_id in self.memories:
                del self.memories[session_id]
                logger.info(f"Memória da sessão {session_id} foi limpa")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao limpar memória: {e}")
            return False
    
    def get_memory_info(self, session_id: str) -> Dict[str, Any]:
        """Obtém informações sobre a memória de uma sessão"""
        try:
            if session_id in self.memories:
                memory = self.memories[session_id]
                messages = memory.chat_memory.messages
                return {
                    "session_id": session_id,
                    "message_count": len(messages),
                    "has_memory": True,
                    "messages": [str(msg) for msg in messages]
                }
            else:
                return {
                    "session_id": session_id,
                    "message_count": 0,
                    "has_memory": False,
                    "messages": []
                }
        except Exception as e:
            logger.error(f"Erro ao obter informações da memória: {e}")
            return {
                "session_id": session_id,
                "error": str(e)
            }
