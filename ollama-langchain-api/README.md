# 🚀 Ollama + LangChain API

Uma API moderna que demonstra como turbinar modelos de IA locais usando LangChain para criar aplicações mais inteligentes e contextuais.

## ✨ Funcionalidades

### 🤖 Chat com IA
- **Chat Simples**: Conversas diretas com modelos Ollama
- **Chat com Contexto**: Adicione contexto adicional para respostas mais precisas
- **Chat com Memória**: Mantenha conversas com histórico entre sessões

### 🔗 LangChain Chains
- **Q&A Chain**: Perguntas e respostas estruturadas
- **Summarize Chain**: Resumo de textos longos
- **Translate Chain**: Tradução entre idiomas

### 🛠️ Utilitários
- **Health Check**: Monitoramento do status da API e Ollama
- **Listagem de Modelos**: Veja todos os modelos disponíveis

## 🎨 Frontend Moderno

A API agora inclui um **frontend moderno e responsivo** com:

- 🎨 **Design Dark Theme** - Perfeito para seus olhos
- 📱 **Interface Responsiva** - Funciona em desktop e mobile
- ⚡ **Navegação por Abas** - Organização intuitiva das funcionalidades
- 🔄 **Chat em Tempo Real** - Interface de chat moderna
- 🎛️ **Controles de Temperatura** - Ajuste a criatividade das respostas
- 🔔 **Notificações Toast** - Feedback visual para o usuário
- 📊 **Indicador de Status** - Monitore se a API está online
- ⏳ **Loading States** - Indicadores visuais durante processamento

### Como Acessar o Frontend

1. **Inicie a API**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Acesse no navegador**:
   ```
   http://127.0.0.1:8000
   ```

3. **Explore as funcionalidades**:
   - Use as abas no menu lateral para navegar
   - Teste o chat simples primeiro
   - Experimente as diferentes chains
   - Verifique o status da API

## 🛠️ Tecnologias

### Backend
- **FastAPI**: Framework web moderno e rápido
- **Ollama**: Para rodar modelos de IA localmente
- **LangChain**: Framework para aplicações de IA
- **Pydantic**: Validação e serialização de dados

### Frontend
- **HTML5**: Estrutura semântica
- **CSS3**: Design moderno com CSS Grid e Flexbox
- **JavaScript ES6+**: Funcionalidade interativa
- **Font Awesome**: Ícones modernos
- **Google Fonts**: Tipografia elegante

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- Ollama instalado
- Modelo de IA baixado (ex: `llama2`)

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
```bash
cp env.example .env
# Edite o arquivo .env conforme necessário
```

### 3. Baixar Modelo Ollama
```bash
ollama pull llama2
```

### 4. Executar a API
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Acessar a Aplicação
- **Frontend**: http://127.0.0.1:8000
- **Documentação API**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

## 📡 Endpoints da API

### Chat
- `POST /chat` - Chat simples
- `POST /chat/context` - Chat com contexto
- `POST /chat/memory` - Chat com memória

### LangChain Chains
- `POST /chat/chain` - Usar chains específicas (qa, summarize, translate)

### Utilitários
- `GET /health` - Health check
- `GET /chat/models` - Listar modelos disponíveis

## 🎯 Exemplos de Uso

### Chat Simples
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá! Como você está?", "temperature": 0.7}'
```

### Chat com Contexto
```bash
curl -X POST "http://127.0.0.1:8000/chat/context" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explique este conceito",
    "context": "Estamos falando sobre inteligência artificial",
    "temperature": 0.7
  }'
```

### Usar LangChain Chain
```bash
curl -X POST "http://127.0.0.1:8000/chat/chain" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Texto para resumir...",
    "chain_type": "summarize"
  }'
```

## 🐳 Docker (Opcional)

### Executar com Docker Compose
```bash
docker-compose up -d
```

### Executar apenas a API
```bash
docker build -t ollama-langchain-api .
docker run -p 8000:8000 ollama-langchain-api
```

## 📁 Estrutura do Projeto

```
ollama-langchain-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicação principal
│   ├── models.py            # Modelos Pydantic
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py          # Rotas de chat
│   └── services/
│       ├── __init__.py
│       └── ollama_service.py # Serviço Ollama
├── static/                  # Frontend
│   ├── index.html          # Página principal
│   ├── styles.css          # Estilos CSS
│   └── script.js           # JavaScript
├── requirements.txt         # Dependências Python
├── env.example             # Exemplo de configuração
├── docker-compose.yml      # Configuração Docker
├── Dockerfile              # Imagem Docker
└── README.md               # Este arquivo
```

## 🎨 Características do Frontend

### Design System
- **Tema Escuro**: Cores suaves para os olhos
- **Gradientes**: Efeitos visuais modernos
- **Animações**: Transições suaves e responsivas
- **Tipografia**: Fonte Inter para melhor legibilidade

### Componentes
- **Sidebar**: Navegação organizada por categorias
- **Chat Interface**: Interface moderna de conversação
- **Form Controls**: Controles intuitivos para parâmetros
- **Toast Notifications**: Feedback não-intrusivo
- **Loading States**: Indicadores visuais de processamento

### Responsividade
- **Desktop**: Layout otimizado para telas grandes
- **Tablet**: Adaptação para telas médias
- **Mobile**: Interface touch-friendly

## 🔧 Configuração Avançada

### Variáveis de Ambiente
```bash
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# API
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=True
```

### Modelos Suportados
- `llama2` (recomendado)
- `mistral`
- `codellama`
- `llama2:7b`
- `llama2:13b`
- `llama2:70b`

## 🚀 Próximos Passos

1. **Teste o Frontend**: Acesse http://127.0.0.1:8000
2. **Experimente as Funcionalidades**: Use todas as abas disponíveis
3. **Personalize**: Modifique cores e estilos no CSS
4. **Adicione Novas Features**: Implemente novas chains ou funcionalidades
5. **Deploy**: Configure para produção

## 📝 Licença

MIT License - veja o arquivo LICENSE para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Enviar pull requests
- Melhorar a documentação

---

**Desenvolvido com ❤️ para demonstrar o poder do Ollama + LangChain**
