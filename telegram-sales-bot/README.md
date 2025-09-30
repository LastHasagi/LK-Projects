# Bot de Vendas Telegram

Bot completo de vendas para Telegram com integração de pagamento, painel administrativo e controle de acesso automatizado.

## Recursos

- 🤖 **Bot Telegram Completo**
  - Catálogo de produtos com imagens
  - Carrinho de compras
  - Sistema de pedidos
  - Notificações automáticas

- 💳 **Integração de Pagamento**
  - PIX (Mercado Pago)
  - Cartão de Crédito
  - Webhooks para confirmação automática
  - QR Code para pagamento PIX

- 🔐 **Controle de Acesso**
  - Links únicos por usuário
  - Acesso temporário ou permanente
  - Remoção automática após expiração
  - Logs de acesso

- 📊 **Painel Administrativo**
  - Dashboard com estatísticas
  - Gerenciamento de produtos
  - Controle de pedidos
  - Gestão de usuários
  - Templates de mensagens personalizáveis
  - Configurações do sistema

- 📧 **Sistema de Mensagens**
  - Templates personalizáveis
  - Lembretes automáticos de pagamento
  - Notificações de expiração de acesso
  - Mensagens de boas-vindas

## Requisitos

- Python 3.11+
- PostgreSQL
- Redis (opcional, para cache)
- Conta no Telegram Bot API
- Conta no Mercado Pago (ou outro gateway)

## Instalação

1. **Clone o repositório**
```bash
git clone <repo-url>
cd telegram-sales-bot
```

2. **Crie o ambiente virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
cp env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Configure o banco de dados**
```bash
# Crie o banco de dados PostgreSQL
createdb telegram_sales_bot

# Execute as migrações
alembic upgrade head
```

6. **Inicie o servidor**
```bash
python -m app.main
```

## Configuração

### Bot do Telegram

1. Crie um bot no [@BotFather](https://t.me/botfather)
2. Copie o token e adicione ao `.env`
3. Configure os comandos do bot:
```
/start - Iniciar o bot
/produtos - Ver produtos disponíveis
/pedidos - Ver meus pedidos
/ajuda - Obter ajuda
```

### Mercado Pago

1. Crie uma conta no [Mercado Pago Developers](https://www.mercadopago.com.br/developers)
2. Obtenha as credenciais (Access Token e Public Key)
3. Configure o webhook URL: `https://seudominio.com/webhook/payment/mercadopago`
4. Adicione as credenciais ao `.env`

### Painel Administrativo

Acesse o painel em `http://localhost:8000/admin`

Credenciais padrão:
- Usuário: `admin`
- Senha: `changeme` (altere no `.env`)

## Uso

### Para Clientes

1. Inicie uma conversa com o bot
2. Use `/produtos` para ver o catálogo
3. Clique em "Comprar" no produto desejado
4. Escolha a forma de pagamento
5. Realize o pagamento
6. Receba o link de acesso automaticamente

### Para Administradores

1. **Produtos**: Adicione produtos com nome, descrição, preço e imagem
2. **Grupos**: Configure o ID do grupo/canal do Telegram para cada produto
3. **Mensagens**: Personalize os templates de mensagens
4. **Pedidos**: Acompanhe todos os pedidos e pagamentos
5. **Usuários**: Gerencie os usuários e acessos

## Estrutura do Projeto

```
telegram-sales-bot/
├── app/
│   ├── models/         # Modelos do banco de dados
│   ├── routers/        # Rotas da API/Admin
│   ├── services/       # Lógica de negócio
│   ├── schemas/        # Schemas Pydantic
│   ├── utils/          # Utilitários
│   ├── config.py       # Configurações
│   ├── database.py     # Conexão com BD
│   └── main.py         # Aplicação principal
├── static/             # Arquivos estáticos
├── templates/          # Templates HTML
├── migrations/         # Migrações Alembic
├── requirements.txt    # Dependências
├── env.example        # Exemplo de configuração
└── README.md          # Este arquivo
```

## API Endpoints

### Autenticação
- `POST /auth/token` - Login
- `POST /auth/logout` - Logout
- `GET /auth/me` - Usuário atual

### Produtos
- `GET /api/products` - Listar produtos
- `GET /api/products/{id}` - Detalhes do produto
- `POST /api/products` - Criar produto (admin)
- `PUT /api/products/{id}` - Atualizar produto (admin)
- `DELETE /api/products/{id}` - Excluir produto (admin)

### Pedidos
- `GET /api/orders` - Listar pedidos (admin)
- `GET /api/orders/{id}` - Detalhes do pedido (admin)

### Webhooks
- `POST /webhook/payment/mercadopago` - Webhook Mercado Pago
- `POST /webhook/telegram` - Webhook Telegram

## Desenvolvimento

### Executar em modo debug
```bash
# No .env
DEBUG=True

# Executar
python -m app.main
```

### Executar testes
```bash
pytest
```

### Criar nova migração
```bash
alembic revision --autogenerate -m "Descrição da mudança"
alembic upgrade head
```

## Deploy

### Docker

```bash
docker-compose up -d
```

### Heroku

```bash
heroku create meu-bot-vendas
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set $(cat .env | grep -v '^#' | xargs)
git push heroku main
```

## Segurança

- Sempre use HTTPS em produção
- Mantenha as credenciais seguras
- Configure firewall para PostgreSQL
- Use senhas fortes
- Ative 2FA nas contas de pagamento
- Faça backup regular do banco de dados

## Suporte

Para suporte, abra uma issue no GitHub ou entre em contato.

## Licença

Este projeto está sob a licença MIT.
