# SETUP.md — EanterOS: Política de Acordos Inteligente

> Guia completo para rodar o projeto do zero. Tempo estimado: **10–15 minutos** (excluindo build da imagem Docker na primeira vez, ~5–8 min).

---

## Quick Start (recomendado)

O script `setup.sh` verifica pré-requisitos, configura o `.env`, sobe todos os containers e aguarda os serviços ficarem prontos:

```bash
git clone https://github.com/ViolanteGabriel/hackathon-ufmg-2026-grupo10.git
cd hackathon-ufmg-2026-grupo10
bash setup.sh
```

O script irá:
1. Verificar Docker, Docker Compose e Git
2. Criar o `.env` a partir do `.env.example` (se não existir)
3. Solicitar a chave da OpenAI interativamente (caso não esteja configurada)
4. Verificar os arquivos do modelo RN1
5. Fazer o build e subir todos os containers (`docker compose up --build -d`)
6. Aguardar os serviços responderem nas portas 8000 e 5173

### Opções do script

```bash
bash setup.sh --no-build   # Sobe os serviços sem reconstruir as imagens (mais rápido)
bash setup.sh --down       # Para e remove todos os containers e volumes
```

Ao final, o script exibe as URLs de acesso e as credenciais de demo.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Verificar |
|---|---|---|
| Docker | 24+ | `docker --version` |
| Docker Compose | v2.20+ | `docker compose version` |
| Git | qualquer | `git --version` |

> **Nota**: Node.js e Python **não** são necessários na máquina host — tudo roda dentro dos containers.

---

## 1. Clonar o repositório

```bash
git clone https://github.com/ViolanteGabriel/hackathon-ufmg-2026-grupo10.git
cd hackathon-ufmg-2026-grupo10
```

---

## 2. Configurar variáveis de ambiente

O `setup.sh` faz isso automaticamente. Para configuração manual:

```bash
cp .env.example .env
```

Abra `.env` e substitua `sk-...` pela chave real:

```env
OPENAI_API_KEY=sk-proj-SUA_CHAVE_AQUI
OPENAI_MODEL_REASONING=gpt-4o-mini
OPENAI_MODEL_EMBEDDING=text-embedding-3-small
POSTGRES_PASSWORD=enteros_dev
JWT_SECRET=change-me-only-for-demo
DATABASE_URL=postgresql+psycopg://enteros:enteros_dev@db:5432/enteros
LOG_LEVEL=INFO
```

> A chave da OpenAI foi fornecida pela organização do hackathon. Sem ela, o pipeline de extração de metadados (Estágio 1) e o GPT Acordo (Estágio 4) não funcionarão — o Estágio 2 (RN1) continua funcionando offline.

---

## 3. Verificar estrutura de dados

Os arquivos de dados fornecidos pela banca devem estar em `data/`. A estrutura esperada:

```
data/
├── raw/                          # criado automaticamente pelo back ao processar uploads
├── processos_exemplo/            # 2 processos de exemplo para demo
│   ├── processo_01/
│   │   ├── autos/                # PDFs dos Autos
│   │   └── subsidios/            # PDFs dos Subsídios
│   └── processo_02/
│       ├── autos/
│       └── subsidios/
└── examples/                     # casos adicionais da banca
```

O modelo de rede neural (RN1) e seus dados de treino já estão versionados:

```
models/
└── litigation_model.pth          # pesos treinados do modelo PyTorch

src/models/RN1/training/
├── resultados_dos_processos.csv  # dataset de treino
└── subsidios_disponibilizados.csv
```

> **Atenção**: `data/` está no `.gitignore` (dados sensíveis). `models/` e `src/models/` são versionados normalmente.

---

## 4. Subir o ambiente completo

**Via script (recomendado):**

```bash
bash setup.sh
```

**Manualmente:**

```bash
docker compose up --build
```

Na **primeira execução**, o build demora mais por causa do PyTorch CPU (~200MB). Nas execuções seguintes, o cache do Docker acelera.

O que acontece em ordem:
1. `db` — PostgreSQL 16 + pgvector sobe e aguarda healthcheck
2. `back` — aguarda o banco, habilita extensão `vector`, executa `alembic upgrade head` (cria tabelas) e sobe o servidor FastAPI
3. `front` — instala dependências Node e sobe o Vite dev server

---

## 5. Acessar o sistema

| Serviço | URL | Descrição |
|---|---|---|
| **Frontend** | http://localhost:5173 | Interface React (Evidence Hub, Decision Lab, Monitoring) |
| **API docs** | http://localhost:8000/docs | Swagger UI — todos os endpoints |
| **API health** | http://localhost:8000/health | Liveness probe |

### Credenciais de demo

| Perfil | Email | Senha | Rota inicial |
|---|---|---|---|
| Advogado | `advogado@banco.com` | `advogado123` | `/home` → Evidence Hub |
| Banco (painel) | `banco@banco.com` | `banco123` | `/monitoring` |

---

## 6. Executar o caminho dourado (demo)

### Fluxo do Advogado

1. Acesse http://localhost:5173 e faça login com `advogado@banco.com`
2. Clique em **Evidence Hub** na sidebar
3. Faça upload dos PDFs de `data/processos_exemplo/processo_01/` (Autos + Subsídios), um de cada vez usando os botões de cada etapa. Clique em **Skip** nos que não tiver arquivo.
4. Clique em **Upload and Analyze** — o pipeline de IA roda automaticamente (~15–30s)
5. Você será redirecionado para o **Decision Lab** com a recomendação da IA:
   - **ACORDO**: mostra valor sugerido, intervalo, custo de litigar e botões ACEITAR / AJUSTAR / RECUSAR
   - **DEFESA**: mostra score de confiança e fatores favoráveis à defesa
6. Clique em um dos botões HITL para registrar a decisão

### Fluxo do Banco

1. Login com `banco@banco.com`
2. Você cai direto no **Monitoring** com métricas em tempo real:
   - Aderência global dos advogados
   - Economia total gerada pelos acordos
   - Feed de recomendações recentes (clicável → abre o caso)
   - Matriz de aderência por advogado

---

## 7. Executar sem Docker (desenvolvimento local)

### Backend

```bash
# Pré-requisitos: Python 3.11+, PostgreSQL 16 rodando localmente

cd src/back
pip install torch scikit-learn numpy --extra-index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev]"

# Configurar variáveis de ambiente
export DATABASE_URL="postgresql+psycopg://enteros:enteros_dev@localhost:5432/enteros"
export OPENAI_API_KEY="sk-proj-..."
export RN1_DIR="../../src/models/RN1"
export RN1_MODEL_PATH="../../models/litigation_model.pth"

# Criar banco e tabelas
alembic upgrade head
# ou, sem alembic, o main.py cria as tabelas automaticamente via SQLAlchemy

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd src/front
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

---

## 8. Variáveis de ambiente — referência completa

| Variável | Descrição | Default |
|---|---|---|
| `OPENAI_API_KEY` | Chave da OpenAI | — (obrigatória) |
| `OPENAI_MODEL_REASONING` | Modelo para extração e valoração | `gpt-4o-mini` |
| `OPENAI_MODEL_EMBEDDING` | Modelo de embeddings para RAG | `text-embedding-3-small` |
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql+psycopg://enteros:enteros_dev@db:5432/enteros` |
| `POSTGRES_PASSWORD` | Senha do banco | `enteros_dev` |
| `JWT_SECRET` | Chave para assinar tokens JWT | `change-me-only-for-demo` |
| `JWT_EXPIRE_MINUTES` | Expiração do token em minutos | `480` (8h) |
| `LOG_LEVEL` | Nível de log (`DEBUG`, `INFO`, `WARNING`) | `INFO` |
| `RN1_DIR` | Caminho para o diretório do modelo RN1 | auto-detectado a partir de `classifier.py` |
| `RN1_MODEL_PATH` | Caminho para `litigation_model.pth` | auto-detectado a partir de `classifier.py` |
| `DATA_DIR` | Diretório raiz para armazenar PDFs enviados | `/data` |

---

## 9. Comandos úteis

```bash
# Setup completo (primeira vez ou após reset)
bash setup.sh

# Setup sem rebuild das imagens (mais rápido)
bash setup.sh --no-build

# Derrubar tudo e recomeçar do zero
bash setup.sh --down && bash setup.sh

# Ver logs de um serviço específico
docker compose logs -f back
docker compose logs -f front

# Reiniciar apenas o backend (ex: após mudança de código)
docker compose restart back

# Parar e remover containers (preserva o volume do banco)
docker compose down

# Parar e apagar TUDO, incluindo banco de dados
docker compose down -v

# Rebuild forçado (ex: após mudar pyproject.toml)
docker compose up --build --force-recreate

# Acessar shell do container do backend
docker compose exec back bash

# Rodar testes do backend
docker compose exec back pytest

# Rodar testes do frontend
docker compose exec front npm test
```

---

## 10. Solução de problemas comuns

### `OPENAI_API_KEY` não definida

```
openai.AuthenticationError: No API key provided.
```

**Solução**: verifique o arquivo `.env` na raiz do projeto. A chave deve começar com `sk-`.

---

### `litigation_model.pth` não encontrado

```
RuntimeError: Falha ao inicializar classificador RN1: ...
```

**Solução**: confirme que `models/litigation_model.pth` existe no repositório. Se necessário, re-clone o repositório. O pipeline continua funcionando com o fallback heurístico (sem o modelo PyTorch).

---

### Banco de dados não conecta

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solução**: aguarde o healthcheck do PostgreSQL passar (~10–15s após `docker compose up`). O backend aguarda automaticamente pelo serviço `db`.

---

### Porta já em uso

```
Error: bind: address already in use
```

**Solução**: algum serviço está usando a porta 5432, 8000 ou 5173. Pare-o ou altere as portas no `docker-compose.yml`.

---

### Build do Docker falha no `torch`

**Solução**: verifique conectividade com `https://download.pytorch.org/whl/cpu`. Em redes corporativas com proxy, adicione ao `docker-compose.yml`:

```yaml
services:
  back:
    build:
      args:
        HTTP_PROXY: http://seu-proxy:porta
        HTTPS_PROXY: http://seu-proxy:porta
```

---

## 11. Arquitetura resumida

```
Browser (React 19 + Vite)
    ↕ axios + TanStack Query (JWT Bearer)
FastAPI (Python 3.11)
    ├── POST /processes          → upload + ingestão de PDFs
    ├── POST /processes/{id}/analyze  → pipeline de IA:
    │       Estágio 1: GPT extrai UF, valor, sub-assunto
    │       Estágio 2: RN1 (PyTorch) → probabilidade de derrota
    │       Estágio 4: GPT Acordo → valor sugerido (se prob > 60%)
    ├── POST /processes/analysis/{id}/decision → HITL do advogado
    └── GET  /dashboard/metrics  → aderência e efetividade
PostgreSQL 16 + pgvector
    └── tabelas: processo, documento, analise_ia, proposta_acordo, decisao_advogado
```

---

> Dúvidas? Abra uma issue no repositório ou consulte o `DEVELOPMENT_CONTEXT.md`.
