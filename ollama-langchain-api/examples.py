import requests
import json
import time
from typing import Dict, Any

# Configurações
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/chat"

def print_response(title: str, response: requests.Response):
    """Função auxiliar para imprimir respostas formatadas"""
    print(f"\n{'='*50}")
    print(f"📋 {title}")
    print(f"{'='*50}")
    print(f"Status: {response.status_code}")
    print(f"Tempo de resposta: {response.headers.get('X-Process-Time', 'N/A')}s")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Resposta: {data.get('response', 'N/A')[:200]}...")
        print(f"🤖 Modelo usado: {data.get('model_used', 'N/A')}")
        print(f"⏱️  Tempo de processamento: {data.get('processing_time', 'N/A')}s")
        if data.get('metadata'):
            print(f"📊 Metadados: {data['metadata']}")
    else:
        print(f"❌ Erro: {response.text}")

def test_simple_chat():
    """Teste de chat simples"""
    print("\n🚀 Testando Chat Simples...")
    
    payload = {
        "message": "Explique o que é machine learning de forma simples",
        "temperature": 0.7
    }
    
    response = requests.post(f"{API_URL}/simple", json=payload)
    print_response("Chat Simples", response)

def test_chat_with_context():
    """Teste de chat com contexto"""
    print("\n🚀 Testando Chat com Contexto...")
    
    payload = {
        "message": "Analise este código Python e sugira melhorias",
        "context": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Teste da função
print(fibonacci(10))
        """,
        "temperature": 0.7
    }
    
    response = requests.post(f"{API_URL}/with-context", json=payload)
    print_response("Chat com Contexto", response)

def test_chat_with_memory():
    """Teste de chat com memória"""
    print("\n🚀 Testando Chat com Memória...")
    
    session_id = "test_session_123"
    
    # Primeira mensagem
    payload1 = {
        "message": "Meu nome é João e eu sou desenvolvedor Python",
        "session_id": session_id,
        "temperature": 0.7
    }
    
    response1 = requests.post(f"{API_URL}/with-memory", json=payload1)
    print_response("Chat com Memória - Mensagem 1", response1)
    
    # Segunda mensagem (deve lembrar do contexto)
    time.sleep(1)
    payload2 = {
        "message": "O que você sabe sobre mim?",
        "session_id": session_id,
        "temperature": 0.7
    }
    
    response2 = requests.post(f"{API_URL}/with-memory", json=payload2)
    print_response("Chat com Memória - Mensagem 2", response2)

def test_qa_chain():
    """Teste de QA chain"""
    print("\n🚀 Testando QA Chain...")
    
    payload = {
        "message": "Qual é a capital do Brasil?",
        "chain_type": "qa",
        "parameters": {
            "context": "O Brasil é o maior país da América do Sul. Sua capital é Brasília, que foi inaugurada em 1960. Antes disso, a capital era o Rio de Janeiro.",
            "temperature": 0.7
        }
    }
    
    response = requests.post(f"{API_URL}/chain", json=payload)
    print_response("QA Chain", response)

def test_summarize_chain():
    """Teste de summarize chain"""
    print("\n🚀 Testando Summarize Chain...")
    
    long_text = """
    A inteligência artificial (IA) é um campo da ciência da computação que se concentra na criação de sistemas capazes de realizar tarefas que normalmente requerem inteligência humana. Essas tarefas incluem aprendizado, raciocínio, resolução de problemas, percepção e linguagem natural. A IA tem aplicações em diversos setores, incluindo saúde, finanças, transporte, educação e entretenimento. Com o avanço da tecnologia, a IA está se tornando cada vez mais sofisticada e integrada em nossas vidas diárias.
    """
    
    payload = {
        "message": long_text,
        "chain_type": "summarize",
        "parameters": {
            "max_length": 100,
            "temperature": 0.7
        }
    }
    
    response = requests.post(f"{API_URL}/chain", json=payload)
    print_response("Summarize Chain", response)

def test_translate_chain():
    """Teste de translate chain"""
    print("\n🚀 Testando Translate Chain...")
    
    payload = {
        "message": "Hello, how are you today?",
        "chain_type": "translate",
        "parameters": {
            "target_language": "português",
            "temperature": 0.7
        }
    }
    
    response = requests.post(f"{API_URL}/chain", json=payload)
    print_response("Translate Chain", response)

def test_code_analysis():
    """Teste de análise de código"""
    print("\n🚀 Testando Análise de Código...")
    
    code = """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def get_history(self):
        return self.history

# Uso da classe
calc = Calculator()
print(calc.add(5, 3))
print(calc.get_history())
    """
    
    payload = {
        "message": "Analise este código e sugira melhorias",
        "context": code,
        "temperature": 0.7
    }
    
    response = requests.post(f"{API_URL}/code-analysis", json=payload)
    print_response("Análise de Código", response)

def test_health_check():
    """Teste de health check"""
    print("\n🚀 Testando Health Check...")
    
    response = requests.get(f"{API_URL}/health")
    print_response("Health Check", response)

def test_list_models():
    """Teste de listagem de modelos"""
    print("\n🚀 Testando Listagem de Modelos...")
    
    response = requests.get(f"{API_URL}/models")
    print_response("Listagem de Modelos", response)

def test_memory_operations():
    """Teste de operações de memória"""
    print("\n🚀 Testando Operações de Memória...")
    
    session_id = "memory_test_456"
    
    # Obter informações da memória (deve estar vazia)
    response1 = requests.get(f"{API_URL}/memory/{session_id}")
    print_response("Informações da Memória (vazia)", response1)
    
    # Adicionar uma mensagem
    payload = {
        "message": "Esta é uma mensagem de teste para memória",
        "session_id": session_id,
        "temperature": 0.7
    }
    
    response2 = requests.post(f"{API_URL}/with-memory", json=payload)
    print_response("Adicionando Mensagem à Memória", response2)
    
    # Obter informações da memória novamente
    response3 = requests.get(f"{API_URL}/memory/{session_id}")
    print_response("Informações da Memória (com dados)", response3)
    
    # Limpar memória
    response4 = requests.delete(f"{API_URL}/memory/{session_id}")
    print_response("Limpando Memória", response4)

def main():
    """Função principal que executa todos os testes"""
    print("🚀 Iniciando Testes da Ollama + LangChain API")
    print("="*60)
    
    try:
        # Teste de conectividade básica
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Erro: Não foi possível conectar à API")
            print(f"Status: {response.status_code}")
            return
        
        print("✅ API está funcionando!")
        
        # Executar todos os testes
        test_health_check()
        test_list_models()
        test_simple_chat()
        test_chat_with_context()
        test_chat_with_memory()
        test_qa_chain()
        test_summarize_chain()
        test_translate_chain()
        test_code_analysis()
        test_memory_operations()
        
        print("\n" + "="*60)
        print("🎉 Todos os testes foram executados!")
        print("📖 Acesse http://localhost:8000/docs para ver a documentação completa")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("💡 Certifique-se de que a API está rodando em http://localhost:8000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()
