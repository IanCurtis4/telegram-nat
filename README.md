# Telegram Adult Content Store Bot MVP

Este projeto é um bot Telegram para venda de conteúdo digital adulto em modelo MVP, com foco em simplicidade, segurança básica e compatibilidade com deploy em container.

## Requisitos

- Python 3.11+
- PostgreSQL
- Bot do Telegram criado via BotFather
- banco PostgreSQL acessível

## Desenvolvimento local

Configure as variáveis de ambiente no shell ou em um arquivo `.env` local.

```env
BOT_TOKEN=
ADMIN_ID=
DATABASE_URL=
DB_ECHO=false
```

Exemplo de execução local em Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

Exemplo em Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

> O arquivo `.env` nunca deve ser enviado ao repositório.

## Deploy no Railway

No serviço da aplicação, configure as seguintes variáveis de ambiente:

```text
BOT_TOKEN
ADMIN_ID
DATABASE_URL
DB_ECHO
```

A aplicação usa `DATABASE_URL` e normaliza automaticamente URLs como `postgresql://` e `postgres://` para `postgresql+asyncpg://` antes de conectar ao SQLAlchemy.

O deploy executa a migração antes do startup:

```text
alembic upgrade head
python -m app.main
```

Não armazene credenciais no código, no repositório ou em arquivos versionados.

## Estrutura do projeto

- `app/` — código do bot
- `migrations/` — schema do Alembic
- `tests/` — testes automatizados

## Segurança

- nunca grave token, senha ou chave no repositório
- use somente `ADMIN_ID` para ações administrativas
- valide transações no servidor e não confie em dados do cliente
- mantenha o bot em long polling neste MVP

## Validação

```bash
python -m compileall app
pytest -q
```
