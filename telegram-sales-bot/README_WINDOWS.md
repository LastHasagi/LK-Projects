# 🚀 Guia Rápido - Windows

Este guia mostra como executar o Bot de Vendas no Windows de forma simples, usando SQLite (sem precisar instalar PostgreSQL).

## 📋 Pré-requisitos

- Python 3.11 ou superior instalado
- Conta no Telegram
- Token do bot (obtenha com @BotFather)

## 🔧 Instalação Rápida

### 1. Abra o PowerShell ou CMD no diretório do projeto

### 2. Crie o ambiente virtual:
```powershell
python -m venv venv
```

### 3. Ative o ambiente virtual:
```powershell
# PowerShell
venv\Scripts\Activate.ps1

# CMD
venv\Scripts\activate.bat
```

### 4. Instale as dependências:
```powershell
pip install -r requirements.txt
```

### 5. Execute o script de configuração local:
```powershell
python run_local.py
```

## 🤖 Configurando o Bot do Telegram

1. **Abra o Telegram e procure por @BotFather**

2. **Crie um novo bot:**
   - Envie: `/newbot`
   - Escolha um nome: `Minha Loja Virtual`
   - Escolha um username: `minha_loja_bot` (deve terminar em 'bot')
   - Copie o token que ele fornecer

3. **Adicione o token no arquivo .env:**
   - Abra o arquivo `.env` no Notepad ou VSCode
   - Substitua `SEU_TOKEN_AQUI` pelo token real
   - Salve o arquivo

## 🎯 Executando o Bot

1. **Execute novamente:**
```powershell
python run_local.py
```

2. **Acesse o painel administrativo:**
   - Abra o navegador em: http://localhost:8000/admin
   - Usuário: `admin`
   - Senha: `admin123`

3. **Teste o bot no Telegram:**
   - Procure seu bot pelo username
   - Envie `/start`

## 📦 Criando seu Primeiro Produto

1. **No painel admin, clique em "Produtos"**
2. **Clique em "Novo Produto"**
3. **Preencha:**
   - Nome: `Curso de Python`
   - Descrição: `Aprenda Python do zero`
   - Preço: `97.00`
   - Deixe o resto como está
4. **Clique em "Salvar"**

## 🎉 Testando uma Venda

1. **No Telegram, envie `/produtos` para seu bot**
2. **Clique em "Comprar"**
3. **Escolha PIX (funciona apenas como demonstração)**

## ⚠️ Limitações do Modo Local

- Pagamentos são apenas simulados (não processa pagamentos reais)
- Não envia pessoas para grupos (precisa configurar)
- Usa SQLite em vez de PostgreSQL
- Adequado apenas para desenvolvimento/testes

## 🚨 Problemas Comuns

### "Module not found"
```powershell
pip install -r requirements.txt
```

### "Permission denied" no PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Bot não responde
- Verifique se o token está correto no .env
- Certifique-se que o servidor está rodando
- Veja os logs no terminal

## 📝 Próximos Passos

1. **Configure um gateway de pagamento real** (Mercado Pago)
2. **Crie grupos no Telegram** para vender acesso
3. **Personalize as mensagens** no painel admin
4. **Faça deploy** em um servidor real

---

**Precisa de ajuda?** Veja o README.md completo ou abra uma issue no GitHub.
