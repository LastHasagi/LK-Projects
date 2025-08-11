// Configurações da API
const API_BASE_URL = 'http://127.0.0.1:8000'; //Se forem usar qualquer coisa em produção, USEM .env PELO AMOR DE DEUS (estou fazendo isso agora de noite, tô morrendo de sono, esqueci como usar .env em JS xD)

// Estado da aplicação
let currentTab = 'simple-chat';
let isApiOnline = false;

// Elementos DOM
const elements = {
    // Navegação
    navButtons: document.querySelectorAll('.nav-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Status
    apiStatus: document.getElementById('api-status'),
    
    // Chat simples
    simpleChatMessages: document.getElementById('simple-chat-messages'),
    simpleChatInput: document.getElementById('simple-chat-input'),
    simpleChatSend: document.getElementById('simple-chat-send'),
    simpleTemperature: document.getElementById('simple-temperature'),
    simpleTempValue: document.getElementById('simple-temp-value'),
    simpleLanguage: document.getElementById('simple-language'),
    
    // Chat com contexto
    contextInput: document.getElementById('context-input'),
    contextMessage: document.getElementById('context-message'),
    contextSend: document.getElementById('context-send'),
    contextTemperature: document.getElementById('context-temperature'),
    contextTempValue: document.getElementById('context-temp-value'),
    contextResponse: document.getElementById('context-response'),
    
    // Chat com memória
    sessionId: document.getElementById('session-id'),
    memoryChatMessages: document.getElementById('memory-chat-messages'),
    memoryChatInput: document.getElementById('memory-chat-input'),
    memoryChatSend: document.getElementById('memory-chat-send'),
    memoryTemperature: document.getElementById('memory-temperature'),
    memoryTempValue: document.getElementById('memory-temp-value'),
    memoryLanguage: document.getElementById('memory-language'),
    
    // Chains
    qaQuestion: document.getElementById('qa-question'),
    qaSend: document.getElementById('qa-send'),
    qaResponse: document.getElementById('qa-response'),
    
    summarizeText: document.getElementById('summarize-text'),
    summarizeSend: document.getElementById('summarize-send'),
    summarizeResponse: document.getElementById('summarize-response'),
    
    translateText: document.getElementById('translate-text'),
    targetLanguage: document.getElementById('target-language'),
    translateSend: document.getElementById('translate-send'),
    translateResponse: document.getElementById('translate-response'),
    
    // Utilitários
    healthCheckBtn: document.getElementById('health-check-btn'),
    healthResponse: document.getElementById('health-response'),
    
    modelsBtn: document.getElementById('models-btn'),
    modelsResponse: document.getElementById('models-response'),
    
    // Overlay e notificações
    loadingOverlay: document.getElementById('loading-overlay'),
    toastContainer: document.getElementById('toast-container')
};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkApiStatus();
});

// Inicialização da aplicação
function initializeApp() {
    // Configurar sliders de temperatura
    setupTemperatureSliders();
    
    // Configurar navegação por abas
    setupTabNavigation();
    
    // Configurar envio por Enter
    setupEnterKeyHandlers();
    
    // Verificar status da API periodicamente
    setInterval(checkApiStatus, 30000); // A cada 30 segundos
}

// Configurar sliders de temperatura
function setupTemperatureSliders() {
    const sliders = [
        { slider: elements.simpleTemperature, display: elements.simpleTempValue },
        { slider: elements.contextTemperature, display: elements.contextTempValue },
        { slider: elements.memoryTemperature, display: elements.memoryTempValue }
    ];
    
    sliders.forEach(({ slider, display }) => {
        if (slider && display) {
            slider.addEventListener('input', (e) => {
                display.textContent = e.target.value;
            });
        }
    });
}

// Configurar navegação por abas
function setupTabNavigation() {
    elements.navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.dataset.tab;
            switchTab(tabId);
        });
    });
}

// Trocar de aba
function switchTab(tabId) {
    // Remover classe active de todos os botões e conteúdos
    elements.navButtons.forEach(btn => btn.classList.remove('active'));
    elements.tabContents.forEach(content => content.classList.remove('active'));
    
    // Adicionar classe active ao botão e conteúdo selecionados
    const activeButton = document.querySelector(`[data-tab="${tabId}"]`);
    const activeContent = document.getElementById(tabId);
    
    if (activeButton && activeContent) {
        activeButton.classList.add('active');
        activeContent.classList.add('active');
        currentTab = tabId;
    }
}

// Configurar handlers para tecla Enter
function setupEnterKeyHandlers() {
    // Chat simples
    if (elements.simpleChatInput) {
        elements.simpleChatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendSimpleChat();
            }
        });
    }
    
    // Chat com memória
    if (elements.memoryChatInput) {
        elements.memoryChatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMemoryChat();
            }
        });
    }
}

// Configurar event listeners
function setupEventListeners() {
    // Chat simples
    if (elements.simpleChatSend) {
        elements.simpleChatSend.addEventListener('click', sendSimpleChat);
    }
    
    // Chat com contexto
    if (elements.contextSend) {
        elements.contextSend.addEventListener('click', sendContextChat);
    }
    
    // Chat com memória
    if (elements.memoryChatSend) {
        elements.memoryChatSend.addEventListener('click', sendMemoryChat);
    }
    
    // Chains
    if (elements.qaSend) {
        elements.qaSend.addEventListener('click', sendQAChain);
    }
    
    if (elements.summarizeSend) {
        elements.summarizeSend.addEventListener('click', sendSummarizeChain);
    }
    
    if (elements.translateSend) {
        elements.translateSend.addEventListener('click', sendTranslateChain);
    }
    
    // Utilitários
    if (elements.healthCheckBtn) {
        elements.healthCheckBtn.addEventListener('click', checkHealth);
    }
    
    if (elements.modelsBtn) {
        elements.modelsBtn.addEventListener('click', listModels);
    }
}

// Verificar status da API
async function checkApiStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (response.ok) {
            updateApiStatus(true);
            isApiOnline = true;
        } else {
            updateApiStatus(false);
            isApiOnline = false;
        }
    } catch (error) {
        updateApiStatus(false);
        isApiOnline = false;
    }
}

// Atualizar indicador de status da API
function updateApiStatus(online) {
    if (elements.apiStatus) {
        if (online) {
            elements.apiStatus.className = 'status online';
            elements.apiStatus.innerHTML = '<i class="fas fa-circle"></i> API Online';
        } else {
            elements.apiStatus.className = 'status offline';
            elements.apiStatus.innerHTML = '<i class="fas fa-circle"></i> API Offline';
        }
    }
}

// Função para gerar instrução de idioma
function getLanguageInstruction(language) {
    const instructions = {
        'pt-BR': 'Por favor, responda sempre em português brasileiro. Seja natural e use expressões comuns do Brasil.',
        'en-US': 'Please respond always in American English. Be natural and use common US expressions.',
        'es-ES': 'Por favor, responde siempre en español de España. Sé natural y usa expresiones comunes de España.'
    };
    return instructions[language] || instructions['pt-BR'];
}

// Funções de chat
async function sendSimpleChat() {
    const message = elements.simpleChatInput.value.trim();
    const temperature = parseFloat(elements.simpleTemperature.value);
    const language = elements.simpleLanguage.value;
    
    if (!message) {
        showToast('Digite uma mensagem', 'warning');
        return;
    }
    
    if (!isApiOnline) {
        showToast('API offline. Verifique se o servidor está rodando.', 'error');
        return;
    }
    
    // Adicionar mensagem do usuário
    addMessage('user', message, elements.simpleChatMessages);
    elements.simpleChatInput.value = '';
    
    showLoading(true);
    
    try {
        // Criar mensagem com instrução de idioma
        const languageInstruction = getLanguageInstruction(language);
        const enhancedMessage = `${languageInstruction}\n\nMensagem do usuário: ${message}`;
        
        const response = await fetch(`${API_BASE_URL}/chat/simple`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: enhancedMessage,
                temperature: temperature
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addMessage('assistant', data.response, elements.simpleChatMessages);
        } else {
            addMessage('system', `Erro: ${data.detail || 'Erro desconhecido'}`, elements.simpleChatMessages);
        }
    } catch (error) {
        addMessage('system', `Erro de conexão: ${error.message}`, elements.simpleChatMessages);
    } finally {
        showLoading(false);
    }
}

async function sendContextChat() {
    const context = elements.contextInput.value.trim();
    const message = elements.contextMessage.value.trim();
    const temperature = parseFloat(elements.contextTemperature.value);
    
    if (!context || !message) {
        showToast('Preencha o contexto e a mensagem', 'warning');
        return;
    }
    
    if (!isApiOnline) {
        showToast('API offline. Verifique se o servidor está rodando.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/with-context`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                context: context,
                temperature: temperature
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResponse(elements.contextResponse, data.response, 'Resposta com Contexto');
        } else {
            showResponse(elements.contextResponse, `Erro: ${data.detail || 'Erro desconhecido'}`, 'Erro', 'error');
        }
    } catch (error) {
        showResponse(elements.contextResponse, `Erro de conexão: ${error.message}`, 'Erro', 'error');
    } finally {
        showLoading(false);
    }
}

async function sendMemoryChat() {
    const sessionId = elements.sessionId.value.trim();
    const message = elements.memoryChatInput.value.trim();
    const temperature = parseFloat(elements.memoryTemperature.value);
    const language = elements.memoryLanguage.value;
    
    if (!sessionId || !message) {
        showToast('Preencha o ID da sessão e a mensagem', 'warning');
        return;
    }
    
    if (!isApiOnline) {
        showToast('API offline. Verifique se o servidor está rodando.', 'error');
        return;
    }
    
    // Adicionar mensagem do usuário
    addMessage('user', message, elements.memoryChatMessages);
    elements.memoryChatInput.value = '';
    
    showLoading(true);
    
    try {
        // Criar mensagem com instrução de idioma
        const languageInstruction = getLanguageInstruction(language);
        const enhancedMessage = `${languageInstruction}\n\nMensagem do usuário: ${message}`;
        
        const response = await fetch(`${API_BASE_URL}/chat/with-memory`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: enhancedMessage,
                session_id: sessionId,
                temperature: temperature
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addMessage('assistant', data.response, elements.memoryChatMessages);
        } else {
            addMessage('system', `Erro: ${data.detail || 'Erro desconhecido'}`, elements.memoryChatMessages);
        }
    } catch (error) {
        addMessage('system', `Erro de conexão: ${error.message}`, elements.memoryChatMessages);
    } finally {
        showLoading(false);
    }
}

// Funções de chains
async function sendQAChain() {
    const question = elements.qaQuestion.value.trim();
    
    if (!question) {
        showToast('Digite uma pergunta', 'warning');
        return;
    }
    
    if (!isApiOnline) {
        showToast('API offline. Verifique se o servidor está rodando.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/chain`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: question,
                chain_type: 'qa'
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResponse(elements.qaResponse, data.response, 'Resposta Q&A');
        } else {
            showResponse(elements.qaResponse, `Erro: ${data.detail || 'Erro desconhecido'}`, 'Erro', 'error');
        }
    } catch (error) {
        showResponse(elements.qaResponse, `Erro de conexão: ${error.message}`, 'Erro', 'error');
    } finally {
        showLoading(false);
    }
}

async function sendSummarizeChain() {
    const text = elements.summarizeText.value.trim();
    
    if (!text) {
        showToast('Digite um texto para resumir', 'warning');
        return;
    }
    
    if (!isApiOnline) {
        showToast('API offline. Verifique se o servidor está rodando.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/chain`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: text,
                chain_type: 'summarize'
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResponse(elements.summarizeResponse, data.response, 'Resumo');
        } else {
            showResponse(elements.summarizeResponse, `Erro: ${data.detail || 'Erro desconhecido'}`, 'Erro', 'error');
        }
    } catch (error) {
        showResponse(elements.summarizeResponse, `Erro de conexão: ${error.message}`, 'Erro', 'error');
    } finally {
        showLoading(false);
    }
}

async function sendTranslateChain() {
    const text = elements.translateText.value.trim();
    const targetLanguage = elements.targetLanguage.value;
    
    if (!text) {
        showToast('Digite um texto para traduzir', 'warning');
        return;
    }
    
    if (!isApiOnline) {
        showToast('API offline. Verifique se o servidor está rodando.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/chain`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: text,
                chain_type: 'translate',
                parameters: {
                    target_language: targetLanguage
                }
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showResponse(elements.translateResponse, data.response, 'Tradução');
        } else {
            showResponse(elements.translateResponse, `Erro: ${data.detail || 'Erro desconhecido'}`, 'Erro', 'error');
        }
    } catch (error) {
        showResponse(elements.translateResponse, `Erro de conexão: ${error.message}`, 'Erro', 'error');
    } finally {
        showLoading(false);
    }
}

// Funções utilitárias
async function checkHealth() {
    if (!isApiOnline) {
        showToast('API offline. Verifique se o servidor está rodando.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/health`);
        const data = await response.json();
        
        if (response.ok) {
            const healthInfo = `
                Status: ${data.status}
                Ollama Status: ${data.ollama_status}
                Modelo Carregado: ${data.model_loaded}
                Timestamp: ${data.timestamp}
            `;
            showResponse(elements.healthResponse, healthInfo, 'Status da API', 'success');
        } else {
            showResponse(elements.healthResponse, `Erro: ${data.detail || 'Erro desconhecido'}`, 'Erro', 'error');
        }
    } catch (error) {
        showResponse(elements.healthResponse, `Erro de conexão: ${error.message}`, 'Erro', 'error');
    } finally {
        showLoading(false);
    }
}

async function listModels() {
    if (!isApiOnline) {
        showToast('API offline. Verifique se o servidor está rodando.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/models`);
        const data = await response.json();
        
        if (response.ok) {
            const modelsList = data.models.map(model => `- ${model.name} (${model.size})`).join('\n');
            showResponse(elements.modelsResponse, modelsList, 'Modelos Disponíveis', 'success');
        } else {
            showResponse(elements.modelsResponse, `Erro: ${data.detail || 'Erro desconhecido'}`, 'Erro', 'error');
        }
    } catch (error) {
        showResponse(elements.modelsResponse, `Erro de conexão: ${error.message}`, 'Erro', 'error');
    } finally {
        showLoading(false);
    }
}

// Funções auxiliares
function addMessage(type, content, container) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const icon = document.createElement('i');
    icon.className = type === 'user' ? 'fas fa-user' : type === 'assistant' ? 'fas fa-robot' : 'fas fa-info-circle';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Formatar o conteúdo adequadamente
    const formattedContent = formatMessageContent(content);
    messageContent.innerHTML = `<p>${formattedContent}</p>`;
    
    messageDiv.appendChild(icon);
    messageDiv.appendChild(messageContent);
    
    container.appendChild(messageDiv);
    
    // Scroll suave para a nova mensagem
    setTimeout(() => {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

// Função para formatar o conteúdo da mensagem
function formatMessageContent(content) {
    // Escapar HTML e preservar quebras de linha
    let formatted = escapeHtml(content);
    
    // Converter URLs em links clicáveis
    formatted = formatted.replace(
        /(https?:\/\/[^\s]+)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: underline;">$1</a>'
    );
    
    // Destacar código inline (texto entre backticks)
    formatted = formatted.replace(
        /`([^`]+)`/g, 
        '<code style="background: rgba(99, 102, 241, 0.1); padding: 0.2em 0.4em; border-radius: 3px; font-family: monospace;">$1</code>'
    );
    
    return formatted;
}

function showResponse(container, content, title, type = 'info') {
    if (!container) return;
    
    container.innerHTML = `
        <h3>${title}</h3>
        <div class="${type}">
            <pre>${escapeHtml(content)}</pre>
        </div>
    `;
    container.classList.add('show');
}

function showLoading(show) {
    if (elements.loadingOverlay) {
        if (show) {
            elements.loadingOverlay.classList.add('show');
        } else {
            elements.loadingOverlay.classList.remove('show');
        }
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = document.createElement('i');
    icon.className = getToastIcon(type);
    
    const text = document.createElement('span');
    text.textContent = message;
    
    toast.appendChild(icon);
    toast.appendChild(text);
    
    elements.toastContainer.appendChild(toast);
    
    // Remover toast após 5 segundos
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 5000);
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return 'fas fa-check-circle';
        case 'error': return 'fas fa-exclamation-circle';
        case 'warning': return 'fas fa-exclamation-triangle';
        case 'info': return 'fas fa-info-circle';
        default: return 'fas fa-info-circle';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Adicionar animação de saída para toasts
const style = document.createElement('style');
style.textContent = `
@keyframes slideOutRight {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(100%);
    }
}
`;
document.head.appendChild(style);
