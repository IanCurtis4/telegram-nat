# Telegram Adult Content Store Bot MVP

Este projeto é um MVP de bot Telegram para venda de conteúdo digital adulto, com foco em segurança básica, clareza de código e facilidade de hospedagem.

## Requisitos

- Python 3.11+
- PostgreSQL
- Bot do Telegram criado com o BotFather
- Banco PostgreSQL acessível

## Configuração local

1. Crie o bot no BotFather e copie o token do bot.
2. Copie o arquivo `.env.example` para `.env`.
3. Configure as variáveis de ambiente:

```bash
cp .env.example .env
```

Edite o `.env` com os valores reais:

```env
BOT_TOKEN=SEU_TOKEN_AQUI
ADMIN_ID=SEU_TELEGRAM_ID
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/telegram_nat
DB_ECHO=false
```

4. Crie um PostgreSQL local e configure a URL do banco.
5. Instale as dependências:

```bash
python -m venv .venv
. .venv/bin/activate  # Linux/macOS
# ou .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

6. Rode as migrations:

```bash
alembic upgrade head
```

7. Inicie o bot:

```bash
python -m app.main
```

8. Cadastre o primeiro produto pelo admin dentro do Telegram.

## Estrutura do projeto

- `app/` — código do bot
- `migrations/` — migrations do Alembic
- `tests/` — testes automatizados

## Desenvolvimento e deploy

- Use `long polling` neste MVP.
- O estado persistente fica no PostgreSQL.
- A aplicação foi pensada para rodar em Railway com um container Docker simples.

## Observações de segurança

- Nunca armazene tokens ou senhas no código.
- Só use `ADMIN_ID` para ações administrativas.
- Nunca confie em dados vindos do cliente para validar transações.

## Testes

```bash
pytest -q
```
