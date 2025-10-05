# Song Recognition - Identificador de Músicas Local

Um aplicativo web que funciona como o Shazam, mas **100% local e offline**, permitindo identificar músicas através da captura de áudio do microfone ou upload de arquivos usando técnicas de fingerprinting de áudio e machine learning.

## 🎵 Funcionalidades

- **Gravação de áudio em tempo real** usando o microfone do dispositivo
- **Upload de arquivos de áudio** para análise
- **Reconhecimento de músicas 100% local** usando fingerprinting de áudio
- **Banco de dados local** para armazenar músicas e suas características
- **Análise avançada de características musicais** (tempo, tonalidade, energia, valência, etc.)
- **Sistema de busca e recomendação** baseado em similaridade
- **Interface web moderna e responsiva**
- **Gerenciamento de playlists**
- **Estatísticas e análise do banco de músicas**

## 🏗️ Arquitetura

O projeto segue o padrão MVC (Model-View-Controller):

- **Models**: Gerenciam dados de áudio e reconhecimentos
- **Views**: Interface web (HTML/CSS/JavaScript)
- **Controllers**: Lógica de negócio para gravação e reconhecimento
- **Services**: Processamento de áudio e integração com APIs

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Microfone (para gravação de áudio)

## 🚀 Instalação

1. **Clone o repositório:**
```bash
git clone <url-do-repositorio>
cd song-recognition
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
```

3. **Ative o ambiente virtual:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

5. **Configure as variáveis de ambiente:**
```bash
# Copie o arquivo de exemplo
copy env.example .env

# Edite o arquivo .env com suas chaves de API
```

## ⚙️ Configuração

### Sistema Local

O sistema funciona **100% offline** e não requer APIs externas:

1. **Banco de dados local**: SQLite para armazenar músicas e fingerprints
2. **Fingerprinting de áudio**: Algoritmos locais para identificação
3. **Análise de características**: Machine learning local para extrair características musicais
4. **Sistema de busca**: Busca por similaridade baseada em características

### Arquivos .gitkeep

Os arquivos `.gitkeep` são usados para manter diretórios vazios no controle de versão do Git:

- `data/.gitkeep`: Mantém o diretório de dados (bancos SQLite são criados automaticamente)
- `temp_audio/.gitkeep`: Mantém o diretório de arquivos temporários
- `static/uploads/.gitkeep`: Mantém o diretório de uploads

**Por que usar .gitkeep?**
- Git não rastreia diretórios vazios
- Esses diretórios são necessários para o funcionamento da aplicação
- O .gitkeep garante que os diretórios existam quando alguém clona o repositório

### Estrutura de Diretórios

```
song-recognition/
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências Python
├── env.example           # Exemplo de configuração
├── controllers/          # Controladores MVC
│   ├── audio_controller.py
│   └── recognition_controller.py
├── models/               # Modelos MVC
│   ├── audio_model.py
│   └── recognition_model.py
├── services/             # Serviços
│   ├── audio_service.py
│   └── recognition_service.py
├── templates/            # Templates HTML
│   └── index.html
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── data/                 # Dados da aplicação
│   ├── .gitkeep         # Mantém diretório no Git
│   ├── music_database.db # Banco principal de músicas
│   └── audio_fingerprints.db # Banco de fingerprints
├── temp_audio/           # Arquivos temporários
│   └── .gitkeep         # Mantém diretório no Git
└── README.md
```

## 🎮 Como Usar

1. **Inicie a aplicação:**
```bash
python app.py
```

2. **Acesse no navegador:**
```
http://localhost:5000
```

3. **Popule o banco de dados:**
```bash
python populate_database.py
```

4. **Identifique uma música:**
   - Clique em "Iniciar Gravação" para gravar do microfone
   - Ou faça upload de um arquivo de áudio
   - Aguarde o processamento e veja o resultado

5. **Gerencie seu banco de músicas:**
   - Use a API para adicionar suas próprias músicas
   - Explore estatísticas e músicas similares
   - Crie playlists personalizadas

## 🔧 Funcionalidades Técnicas

### Processamento de Áudio

- **Extração de características**: MFCC, Spectral Centroid, Zero Crossing Rate, etc.
- **Análise de tempo**: Detecção de BPM
- **Análise espectral**: Frequências e energia
- **Suporte a múltiplos formatos**: WAV, MP3, M4A

### Reconhecimento de Músicas

1. **Fingerprinting Local**: Sistema principal de reconhecimento usando hashes de áudio
2. **Análise de Características**: Extração de características musicais (tempo, tonalidade, energia, etc.)
3. **Banco de Dados Local**: Armazenamento e busca de músicas conhecidas
4. **Machine Learning**: Classificação de gênero e análise de similaridade

### Interface Web

- **Design responsivo**: Funciona em desktop e mobile
- **Gravação em tempo real**: Indicadores visuais de gravação
- **Upload de arquivos**: Suporte a drag & drop
- **Histórico**: Salva identificações anteriores
- **Notificações**: Feedback visual para o usuário

## 📚 Bibliotecas Utilizadas

- **Flask**: Framework web
- **librosa**: Processamento de áudio
- **pydub**: Manipulação de áudio
- **soundfile**: Leitura/escrita de arquivos de áudio
- **numpy**: Computação numérica
- **requests**: Chamadas HTTP para APIs

## 🛠️ Desenvolvimento

### Estrutura MVC

**Models:**
- `AudioModel`: Gerencia dados de gravações
- `RecognitionModel`: Gerencia resultados de reconhecimento

**Controllers:**
- `AudioController`: Controla gravação e processamento
- `RecognitionController`: Controla reconhecimento de músicas

**Services:**
- `AudioService`: Processamento e extração de características
- `RecognitionService`: Integração com APIs externas

### Adicionando Novos Serviços

Para adicionar um novo serviço de reconhecimento:

1. Crie uma nova classe em `services/`
2. Implemente o método `recognize()`
3. Adicione a integração no `RecognitionService`
4. Configure as variáveis de ambiente necessárias

## 🚨 Limitações

- **Banco de dados local**: Precisa ser populado com músicas conhecidas
- **Qualidade do áudio**: Afeta a precisão do reconhecimento
- **Navegadores**: Alguns podem ter limitações de microfone
- **Processamento**: Análise de áudio pode ser computacionalmente intensiva
- **Precisão**: Depende da qualidade do banco de dados local

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Verifique a documentação das APIs utilizadas
- Consulte os logs da aplicação

## 🔮 Roadmap

- [ ] Suporte a mais formatos de áudio
- [ ] Integração com Spotify/Apple Music --> Isso aqui dá pra fazer uma parada maneira, assim que reconhecer a música, ele já te manda o nome e o link do spotify, fica mt maneiro
- [ ] Análise de sentimento musical
- [ ] Reconhecimento de gêneros mais preciso
- [ ] API REST para integração externa
- [ ] Aplicativo mobile

# Documentos usados como base
* https://drive.google.com/file/d/1ahyCTXBAZiuni6RTzHzLoOwwfTRFaU-C/view
* https://hajim.rochester.edu/ece/sites/zduan/teaching/ece472/projects/2019/AudioFingerprinting.pdf
* https://www.toptal.com/algorithms/shazam-it-music-processing-fingerprinting-and-recognition
* https://www.royvanrijn.com/blog/2010/06/creating-shazam-in-java
* https://www.youtube.com/watch?v=a0CVCcb0RJM

# Créditos

Esse projeto foi inspirado no projeto do Chigozirim, por um vídeo que ele fez mostrando como recriou o Shazam.