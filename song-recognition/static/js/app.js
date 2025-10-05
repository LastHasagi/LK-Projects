// Aplicação JavaScript para Song Recognition
class SongRecognitionApp {
    constructor() {
        this.isRecording = false;
        this.recordingStartTime = null;
        this.recordingTimer = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        this.initializeElements();
        this.attachEventListeners();
        this.checkMicrophoneSupport();
    }
    
    initializeElements() {
        this.recordBtn = document.getElementById('recordBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.audioFile = document.getElementById('audioFile');
        this.recordingIndicator = document.getElementById('recordingIndicator');
        this.recordingTimer = document.getElementById('recordingTimer');
        this.resultSection = document.getElementById('resultSection');
        this.resultContent = document.getElementById('resultContent');
        this.historyContent = document.getElementById('historyContent');
        this.loadHistoryBtn = document.getElementById('loadHistoryBtn');
        this.loadingModal = document.getElementById('loadingModal');
        this.loadingText = document.getElementById('loadingText');
        this.toastContainer = document.getElementById('toastContainer');
    }
    
    attachEventListeners() {
        this.recordBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.uploadBtn.addEventListener('click', () => this.uploadAndAnalyze());
        this.audioFile.addEventListener('change', () => this.handleFileSelect());
        this.loadHistoryBtn.addEventListener('click', () => this.loadHistory());
    }
    
    async checkMicrophoneSupport() {
        try {
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                console.log('Microfone suportado');
            } else {
                this.showToast('Seu navegador não suporta gravação de áudio', 'error');
                this.recordBtn.disabled = true;
            }
        } catch (error) {
            console.error('Erro ao verificar suporte ao microfone:', error);
            this.showToast('Erro ao acessar microfone', 'error');
        }
    }
    
    async startRecording() {
        try {
            this.showLoading('Iniciando gravação...');
            
            // Tentar usar MediaRecorder API primeiro
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.mediaRecorder = new MediaRecorder(stream);
                this.audioChunks = [];
                
                this.mediaRecorder.ondataavailable = (event) => {
                    this.audioChunks.push(event.data);
                };
                
                this.mediaRecorder.onstop = () => {
                    this.processRecording();
                };
                
                this.mediaRecorder.start();
                this.isRecording = true;
                this.recordingStartTime = Date.now();
                
                this.updateRecordingUI(true);
                this.startTimer();
                this.hideLoading();
                
                this.showToast('Gravação iniciada!', 'success');
            } else {
                // Fallback para API do servidor
                await this.startServerRecording();
            }
        } catch (error) {
            console.error('Erro ao iniciar gravação:', error);
            this.showToast('Erro ao iniciar gravação: ' + error.message, 'error');
            this.hideLoading();
        }
    }
    
    async startServerRecording() {
        try {
            const response = await fetch('/record', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.isRecording = true;
                this.recordingStartTime = new Date(result.start_time);
                this.updateRecordingUI(true);
                this.startTimer();
                this.hideLoading();
                this.showToast('Gravação iniciada!', 'success');
            } else {
                throw new Error(result.error || 'Erro desconhecido');
            }
        } catch (error) {
            console.error('Erro na gravação do servidor:', error);
            this.showToast('Erro ao iniciar gravação: ' + error.message, 'error');
            this.hideLoading();
        }
    }
    
    async stopRecording() {
        try {
            this.showLoading('Processando gravação...');
            
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
                this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            } else {
                // Fallback para API do servidor
                await this.stopServerRecording();
            }
            
            this.isRecording = false;
            this.updateRecordingUI(false);
            this.stopTimer();
            
        } catch (error) {
            console.error('Erro ao parar gravação:', error);
            this.showToast('Erro ao parar gravação: ' + error.message, 'error');
            this.hideLoading();
        }
    }
    
    async stopServerRecording() {
        try {
            const response = await fetch('/stop_record', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Simular processamento de áudio
                setTimeout(() => {
                    this.processServerRecording(result.audio_info);
                }, 2000);
            } else {
                throw new Error(result.error || 'Erro desconhecido');
            }
        } catch (error) {
            console.error('Erro ao parar gravação do servidor:', error);
            this.showToast('Erro ao parar gravação: ' + error.message, 'error');
            this.hideLoading();
        }
    }
    
    async processRecording() {
        try {
            this.showLoading('Analisando áudio...');
            
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            
            const response = await fetch('/recognize', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            this.displayResult(result);
            this.hideLoading();
            
        } catch (error) {
            console.error('Erro ao processar gravação:', error);
            this.showToast('Erro ao processar gravação: ' + error.message, 'error');
            this.hideLoading();
        }
    }
    
    async processServerRecording(audioInfo) {
        try {
            this.showLoading('Reconhecendo música...');
            
            // Simular chamada para reconhecimento
            const mockResult = {
                success: Math.random() > 0.5,
                service_used: 'Mock Service',
                song_info: {
                    title: 'Música de Exemplo',
                    artist: 'Artista Exemplo',
                    album: 'Álbum Exemplo',
                    release_date: '2023'
                },
                confidence: 0.85,
                message: 'Música reconhecida com sucesso!'
            };
            
            // Simular delay de processamento
            setTimeout(() => {
                this.displayResult(mockResult);
                this.hideLoading();
            }, 3000);
            
        } catch (error) {
            console.error('Erro ao processar gravação do servidor:', error);
            this.showToast('Erro ao processar gravação: ' + error.message, 'error');
            this.hideLoading();
        }
    }
    
    handleFileSelect() {
        const file = this.audioFile.files[0];
        if (file) {
            this.uploadBtn.disabled = false;
            this.showToast('Arquivo selecionado: ' + file.name, 'success');
        } else {
            this.uploadBtn.disabled = true;
        }
    }
    
    async uploadAndAnalyze() {
        const file = this.audioFile.files[0];
        if (!file) {
            this.showToast('Selecione um arquivo de áudio primeiro', 'error');
            return;
        }
        
        try {
            this.showLoading('Analisando arquivo...');
            
            const formData = new FormData();
            formData.append('audio', file);
            
            const response = await fetch('/recognize', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            this.displayResult(result);
            this.hideLoading();
            
        } catch (error) {
            console.error('Erro ao analisar arquivo:', error);
            this.showToast('Erro ao analisar arquivo: ' + error.message, 'error');
            this.hideLoading();
        }
    }
    
    displayResult(result) {
        this.resultSection.classList.remove('hidden');
        
        if (result.success) {
            this.resultContent.innerHTML = this.createSuccessResultHTML(result);
        } else {
            this.resultContent.innerHTML = this.createErrorResultHTML(result);
        }
        
        // Scroll para o resultado
        this.resultSection.scrollIntoView({ behavior: 'smooth' });
        
        // Mostrar toast baseado no resultado
        if (result.success) {
            this.showToast('Música identificada com sucesso!', 'success');
        } else {
            this.showToast('Não foi possível identificar a música', 'error');
        }
    }
    
    createSuccessResultHTML(result) {
        const songInfo = result.song_info;
        const confidence = Math.round(result.confidence * 100);
        
        return `
            <div class="song-info">
                <div class="song-cover">
                    <i class="fas fa-music"></i>
                </div>
                <div class="song-details">
                    <h3>${songInfo.title}</h3>
                    <p><strong>Artista:</strong> ${songInfo.artist}</p>
                    ${songInfo.album ? `<p><strong>Álbum:</strong> ${songInfo.album}</p>` : ''}
                    ${songInfo.release_date ? `<p><strong>Ano:</strong> ${songInfo.release_date}</p>` : ''}
                    ${songInfo.tempo ? `<p><strong>Tempo:</strong> ${Math.round(songInfo.tempo)} BPM</p>` : ''}
                    ${songInfo.estimated_genre ? `<p><strong>Gênero Estimado:</strong> ${songInfo.estimated_genre}</p>` : ''}
                </div>
            </div>
            <div class="confidence-bar">
                <div class="confidence-label">Confiança: ${confidence}%</div>
                <div class="confidence-progress">
                    <div class="confidence-fill" style="width: ${confidence}%"></div>
                </div>
            </div>
            <p class="mt-20"><strong>Serviço usado:</strong> ${result.service_used}</p>
        `;
    }
    
    createErrorResultHTML(result) {
        return `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Não foi possível identificar a música</h3>
                <p>${result.message}</p>
                <p><strong>Sugestões:</strong></p>
                <ul>
                    <li>Certifique-se de que a música está tocando claramente</li>
                    <li>Tente gravar por mais tempo (10-15 segundos)</li>
                    <li>Reduza o ruído de fundo</li>
                    <li>Tente novamente em alguns segundos</li>
                </ul>
            </div>
        `;
    }
    
    async loadHistory() {
        try {
            this.showLoading('Carregando histórico...');
            
            // Simular carregamento de histórico
            const mockHistory = [
                {
                    id: '1',
                    song_info: {
                        title: 'Bohemian Rhapsody',
                        artist: 'Queen',
                        album: 'A Night at the Opera'
                    },
                    created_at: new Date().toISOString(),
                    confidence: 0.95
                },
                {
                    id: '2',
                    song_info: {
                        title: 'Imagine',
                        artist: 'John Lennon',
                        album: 'Imagine'
                    },
                    created_at: new Date(Date.now() - 86400000).toISOString(),
                    confidence: 0.87
                }
            ];
            
            setTimeout(() => {
                this.displayHistory(mockHistory);
                this.hideLoading();
            }, 1000);
            
        } catch (error) {
            console.error('Erro ao carregar histórico:', error);
            this.showToast('Erro ao carregar histórico: ' + error.message, 'error');
            this.hideLoading();
        }
    }
    
    displayHistory(history) {
        if (history.length === 0) {
            this.historyContent.innerHTML = '<p class="text-center">Nenhum histórico encontrado</p>';
            return;
        }
        
        const historyHTML = history.map(item => `
            <div class="history-item">
                <h4>${item.song_info.title}</h4>
                <p><strong>Artista:</strong> ${item.song_info.artist}</p>
                ${item.song_info.album ? `<p><strong>Álbum:</strong> ${item.song_info.album}</p>` : ''}
                <p><strong>Confiança:</strong> ${Math.round(item.confidence * 100)}%</p>
                <div class="history-date">${new Date(item.created_at).toLocaleString('pt-BR')}</div>
            </div>
        `).join('');
        
        this.historyContent.innerHTML = historyHTML;
    }
    
    updateRecordingUI(recording) {
        this.recordBtn.disabled = recording;
        this.stopBtn.disabled = !recording;
        
        if (recording) {
            this.recordingIndicator.classList.remove('hidden');
        } else {
            this.recordingIndicator.classList.add('hidden');
        }
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            this.recordingTimer.textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            this.recordingTimer.classList.remove('hidden');
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        this.recordingTimer.classList.add('hidden');
    }
    
    showLoading(text = 'Processando...') {
        this.loadingText.textContent = text;
        this.loadingModal.classList.remove('hidden');
    }
    
    hideLoading() {
        this.loadingModal.classList.add('hidden');
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        this.toastContainer.appendChild(toast);
        
        // Mostrar toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remover toast após 5 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 5000);
    }
}

// Inicializar aplicação quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new SongRecognitionApp();
});
