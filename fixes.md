Estou preparando este projeto para o primeiro deploy real no Railway.

Repositório: `IanCurtis4/telegram-nat`

O projeto já possui:

* Python 3.11
* aiogram 3.13.0
* SQLAlchemy async
* asyncpg
* Alembic
* PostgreSQL
* Dockerfile
* railway.json
* handlers do Telegram
* catálogo
* administração
* pagamentos em Telegram Stars
* migration inicial

Não quero que você refaça a arquitetura. Quero apenas preparar e validar o projeto para que ele consiga subir corretamente.

IMPORTANTE: NÃO crie, altere ou tente descobrir credenciais reais.

Eu configurarei manualmente no ambiente de execução:

* `BOT_TOKEN`
* `ADMIN_ID`
* `DATABASE_URL`
* `DB_ECHO`

O token real atualmente existe apenas na minha máquina sob outro nome de variável, mas o projeto deve continuar usando genericamente `BOT_TOKEN`.

Não coloque nenhuma credencial no Git, em `.env.example`, testes, README ou código.

## Tarefa 1 — Corrigir inicialização do aiogram

O projeto usa:

`aiogram==3.13.0`

Verifique `app/main.py`.

Se existir algo como:

```python
Bot(
    token=settings.bot_token,
    parse_mode=ParseMode.HTML,
)
```

corrija para a API apropriada do aiogram 3.13.

Use `DefaultBotProperties`.

A forma esperada é conceitualmente:

```python
from aiogram.client.default import DefaultBotProperties

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
    ),
)
```

Verifique os imports e remova imports que ficarem desnecessários.

Não altere o comportamento do bot além do necessário.

## Tarefa 2 — Normalizar DATABASE_URL

O projeto usa SQLAlchemy assíncrono + asyncpg.

O SQLAlchemy deve receber uma URL usando o driver:

```text
postgresql+asyncpg://
```

Porém provedores como Railway podem fornecer:

```text
postgresql://
```

ou eventualmente:

```text
postgres://
```

Quero que `app/config.py` normalize automaticamente essas URLs.

Comportamento esperado:

```text
postgresql://user:pass@host/db
→
postgresql+asyncpg://user:pass@host/db
```

e:

```text
postgres://user:pass@host/db
→
postgresql+asyncpg://user:pass@host/db
```

Se já vier:

```text
postgresql+asyncpg://
```

não altere nada.

Faça essa transformação em uma função pequena e testável, em vez de deixar lógica espalhada.

Algo conceitualmente semelhante a:

```python
def normalize_database_url(url: str) -> str:
    ...
```

Não use manipulações perigosas que possam alterar usuário, senha, host, query params ou caracteres escapados da URL.

## Tarefa 3 — Testar configuração

Atualize ou adicione testes para garantir:

1. `BOT_TOKEN` continua obrigatório.
2. `ADMIN_ID` continua obrigatório e inteiro positivo.
3. `DATABASE_URL` continua obrigatório.
4. `postgresql://` vira `postgresql+asyncpg://`.
5. `postgres://` vira `postgresql+asyncpg://`.
6. `postgresql+asyncpg://` permanece inalterado.
7. `DB_ECHO=true` continua funcionando.
8. nenhum secret aparece em mensagens de erro.

Não use uma conexão PostgreSQL real nesses testes.

## Tarefa 4 — Migration automática no Railway

Examine `railway.json`.

Quero que as migrations sejam aplicadas automaticamente antes da inicialização de uma nova versão.

Adicione, se compatível com a configuração atual do Railway:

```json
"preDeployCommand": "alembic upgrade head"
```

Mantendo:

```json
"startCommand": "python -m app.main"
```

Não remova a política de restart existente.

O resultado conceitual deve ser:

```text
build
↓
alembic upgrade head
↓
python -m app.main
```

Se a sintaxe atual do arquivo estiver incorreta ou desatualizada, corrija preservando a intenção.

## Tarefa 5 — Revisar o Dockerfile

Examine o Dockerfile atual.

Ele deve continuar simples e adequado a Railway.

Garanta que:

* usa Python 3.11 slim ou equivalente;
* define um diretório de trabalho;
* instala `requirements.txt`;
* copia o projeto;
* executa `python -m app.main`;
* não contém secrets;
* não depende de arquivos locais persistentes;
* funciona com variáveis de ambiente fornecidas externamente.

Não adicione nginx, supervisor, systemd ou outras camadas desnecessárias.

Este bot usa long polling e não precisa expor uma porta HTTP.

## Tarefa 6 — Validar Alembic

Confirme que:

```bash
alembic upgrade head
```

usa o mesmo `DATABASE_URL` fornecido por `app.config`.

Confira:

* `alembic.ini`
* `migrations/env.py`
* migration inicial
* imports de `Base`
* metadata

Garanta que o Alembic também recebe a URL já normalizada para asyncpg.

Não gere uma migration nova se o schema atual e a migration existente já estiverem alinhados.

## Tarefa 7 — Startup e shutdown

Revise `app/main.py`.

Mantenha long polling.

Quero um startup simples e robusto.

Verifique:

* inicialização correta do Bot;
* inicialização correta do Dispatcher;
* routers registrados;
* `delete_webhook` antes de polling;
* encerramento limpo;
* logs sem secrets.

Se fizer sentido para a versão atual do aiogram, garanta que a sessão HTTP do Bot seja fechada corretamente quando o polling terminar.

Não transforme o projeto em webhook.

## Tarefa 8 — Verificar imports e erros óbvios

Faça uma revisão do projeto procurando:

* imports quebrados;
* referências a arquivos inexistentes;
* módulos que não são registrados;
* incompatibilidades com aiogram 3.13;
* uso incorreto de APIs async;
* problemas óbvios de SQLAlchemy;
* erros que impediriam o startup;
* tipos incompatíveis nas models;
* callbacks registrados incorretamente.

Não faça uma refatoração geral.

Corrija somente problemas concretos encontrados.

## Tarefa 9 — Atualizar README

Atualize o README para deixar claro que existem dois cenários.

### Desenvolvimento local

O usuário precisa configurar:

```env
BOT_TOKEN=
ADMIN_ID=
DATABASE_URL=
DB_ECHO=false
```

Depois:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

Inclua também equivalente Linux/macOS se já houver documentação multiplataforma.

### Railway

Explique somente que no serviço da aplicação devem existir:

```text
BOT_TOKEN
ADMIN_ID
DATABASE_URL
DB_ECHO
```

Não coloque valores reais.

Explique que `DATABASE_URL` deve apontar para o serviço PostgreSQL e que o código normaliza automaticamente a URL para asyncpg.

Explique também que o deploy executa:

```text
alembic upgrade head
```

antes de:

```text
python -m app.main
```

Não escreva instruções que envolvam colocar secrets dentro do repositório.

## Tarefa 10 — Executar validações

Depois das alterações, rode tudo que puder localmente sem precisar das credenciais reais.

Quero pelo menos:

```bash
python -m compileall app
pytest -q
```

Se houver lint configurado no projeto, rode também.

Não tente iniciar o bot usando tokens fictícios.

Se algum teste falhar:

1. investigue;
2. corrija se for consequência das alterações;
3. rode novamente.

## Limites desta tarefa

NÃO faça:

* criação de conta Railway;
* criação de serviço PostgreSQL;
* configuração de variables no painel Railway;
* geração ou rotação do token BotFather;
* tentativa de descobrir meu `ADMIN_ID`;
* commit de `.env`;
* criação de secrets fictícios;
* troca para webhook;
* Redis;
* painel web;
* refatoração arquitetural ampla;
* novas features de vendas.

Essas partes ficam fora do escopo.

## Resultado esperado

Ao terminar, quero que o repositório esteja em um estado no qual eu precise fazer manualmente apenas:

1. fornecer `BOT_TOKEN`;
2. fornecer `ADMIN_ID`;
3. fornecer um PostgreSQL via `DATABASE_URL`;
4. fazer o deploy.

O código deve cuidar do restante.

Antes de editar, examine os arquivos atuais.

Depois faça as alterações diretamente no workspace.

Ao final, me informe de forma curta:

* arquivos modificados;
* bugs encontrados;
* testes executados;
* resultado dos testes;
* quaisquer passos que ainda dependam exclusivamente de mim.

Comece agora.
