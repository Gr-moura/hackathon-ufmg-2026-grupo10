# EanterOS — Política de Acordos Inteligente

> Solução desenvolvida pelo **Grupo 10** para o Hackathon UFMG 2026 (cliente: Banco UFMG).
> Automatiza e monitora decisões de acordo/defesa em casos de não reconhecimento de contratação de empréstimo.

---

## O Problema

O Banco UFMG recebe ~5.000 processos/mês onde clientes alegam não reconhecer a contratação de um empréstimo. Para cada processo, um advogado externo decide: **propor acordo** ou **ir à defesa**. Sem ferramenta, essa decisão é subjetiva, lenta e impossível de monitorar em escala.

## Nossa Solução

O **EanterOS** é um sistema que:

1. Recebe os documentos do processo (Autos + Subsídios) via upload guiado
2. Executa um pipeline de IA que analisa os documentos e emite recomendação fundamentada
3. Apresenta ao advogado: decisão (ACORDO/DEFESA), valor sugerido, confiança e citações dos documentos
4. Registra a decisão do advogado para monitoramento de aderência e efetividade

---

## Requisitos Atendidos

| Requisito | Como é atendido |
|-----------|----------------|
| **Regra de decisão** | Pipeline: RN1 (PyTorch, treinada em 60k sentenças históricas) + RAG per-processo + GPT-4o-mini (`llm_classifier`) com Structured Outputs |
| **Sugestão de valor** | Valuator GPT calcula `valor_sugerido`, `intervalo_min/max` e `economia_esperada` com base na `policy.yaml` e nos trechos recuperados pelo RAG |
| **Acesso à recomendação** | Decision Lab (frontend React) com recomendação, confiança, trechos citados e fatores pró/contra |
| **Monitoramento de aderência** | Toda decisão do advogado é gravada (aceite/ajuste/recusa), com justificativa obrigatória quando há ajuste significativo e timestamp |
| **Monitoramento de efetividade** | Dashboard executivo com taxa de acordos, economia acumulada, drift de confiança e alertas por advogado |

---

## Credenciais de Acesso (demo)

| Perfil | E-mail | Senha |
|--------|--------|-------|
| Advogado | `advogado@banco.com` | `advogado123` |
| Banco (gestor) | `banco@banco.com` | `banco123` |

As credenciais estão em `src/back/app/core/security.py` e são apenas para demonstração.

---

## Rodando com Docker (recomendado)

### Pré-requisitos

- Docker Engine 24+
- Docker Compose v2

### 1. Clone o repositório

```bash
git clone https://github.com/Gr-moura/hackathon-ufmg-2026-grupo10.git
cd hackathon-ufmg-2026-grupo10
```

### 2. Configure o `.env`

```bash
cp .env.example .env
```

Edite `.env` e preencha, no mínimo, a chave da OpenAI:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL_REASONING=gpt-4o-mini
OPENAI_MODEL_EMBEDDING=text-embedding-3-small
POSTGRES_PASSWORD=enteros_dev
JWT_SECRET=change-me-only-for-demo
DATABASE_URL=postgresql+psycopg://enteros:enteros_dev@db:5432/enteros
LOG_LEVEL=INFO
```

### 3. Suba os containers

```bash
docker compose up --build
```

O serviço `back` executa `alembic upgrade head` antes de iniciar o Uvicorn, e o `Base.metadata.create_all` é chamado no `startup` da aplicação para garantir o schema. A extensão `pgvector` já vem habilitada na imagem `pgvector/pgvector:pg16`; caso você rode um Postgres manual, execute `CREATE EXTENSION IF NOT EXISTS vector;` (ver `src/back/scripts/init_db.sh`).

### 4. Acesse

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend (Swagger) | http://localhost:8000/docs |
| Backend (ReDoc) | http://localhost:8000/redoc |
| Healthcheck | http://localhost:8000/health |
| PostgreSQL | `localhost:5432` (usuário: `enteros`, DB: `enteros`) |

### 5. (Opcional) Popular dados históricos para demo

```bash
# Popula a tabela sentenca_historica a partir do CSV de 60k sentenças
docker compose exec back python scripts/seed_sentencas.py --csv /data/sentencas.csv

# Popula métricas/decisões de advogados para exibir o dashboard executivo
docker compose exec back python scripts/seed_mock_metrics.py
```

---

## Rodando Localmente (sem Docker)

### Pré-requisitos

- Python 3.11+ (o backend declara `requires-python = ">=3.11"`)
- Node.js 18+
- PostgreSQL 16 com extensão `pgvector`
- Tesseract OCR com pacote `por` (para fallback de OCR em PDFs escaneados)

### Backend

```bash
cd src/back

# Crie e ative o virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Instale as dependências (inclui extras de dev)
pip install -e ".[dev]"

# Prepare o banco
createdb enteros
psql -d enteros -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Crie o .env local (copie do .env.example na raiz e ajuste a DATABASE_URL)
cat > .env << EOF
DATABASE_URL=postgresql+psycopg://seu_usuario:sua_senha@localhost:5432/enteros
OPENAI_API_KEY=sk-...
OPENAI_MODEL_REASONING=gpt-4o-mini
OPENAI_MODEL_EMBEDDING=text-embedding-3-small
JWT_SECRET=change-me-only-for-demo
LOG_LEVEL=INFO
EOF

# Execute as migrações
alembic upgrade head

# Inicie o servidor
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd src/front
npm install

# Configure a URL do backend
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

npm run dev
```

Acesse http://localhost:5173.

---

## Fluxo de Uso

### Perfil: Advogado

1. **Login** (`/login`) com `advogado@banco.com`
2. **Início** (`/home`) — visão geral das capacidades e atalhos
3. **Central de Evidências** (`/upload`): upload sequencial dos documentos do processo — a interface guia documento a documento, permitindo **"Pular e marcar como ausente"** quando o arquivo não estiver disponível
4. **Mesa de Decisão** (`/processes`): lista dos processos criados; clique em um processo para abrir o Decision Lab
5. **Decision Lab** (`/dashboard/:processoId`): visualiza a recomendação da IA — decisão, nível de confiança, valor sugerido com intervalo, fatores pró-acordo e pró-defesa, trechos citados dos documentos
6. **HITL**: aceita, ajusta (com justificativa obrigatória quando o ajuste for significativo) ou recusa a recomendação

### Perfil: Banco (Gestor)

1. **Login** (`/login`) com `banco@banco.com`
2. **Início** (`/home`) — visão geral
3. **Monitoramento** (`/monitoring`): acompanha métricas globais — total de processos, aderência por advogado, economia acumulada vs. condenações, casos de alto risco (baixa confiança) e feed das últimas recomendações

---

## Estrutura do Projeto

```
hackathon-ufmg-2026-grupo10/
├── src/
│   ├── back/                        # API FastAPI (Python 3.11+)
│   │   ├── app/
│   │   │   ├── main.py              # App + CORS + routers + create_all
│   │   │   ├── config.py            # Settings via Pydantic BaseSettings
│   │   │   ├── deps.py              # OAuth2 + SQLAlchemy session DI
│   │   │   ├── core/                # security (JWT/hash), logging, exceptions
│   │   │   ├── db/
│   │   │   │   ├── base.py / session.py
│   │   │   │   └── models/          # processo, documento, analise_ia,
│   │   │   │                        # decisao_advogado, proposta_acordo,
│   │   │   │                        # sentenca_historica
│   │   │   ├── routers/             # auth, processes, analysis, metrics
│   │   │   ├── schemas/             # Pydantic request/response models
│   │   │   ├── services/
│   │   │   │   ├── ai/              # pipeline, extractor, classifier,
│   │   │   │   │                    # valuator, llm_classifier, retriever,
│   │   │   │   │                    # prompts/
│   │   │   │   ├── ingestion/       # pdf, ocr, xlsx
│   │   │   │   └── metrics/         # aggregator
│   │   │   └── tests/               # testes do módulo app
│   │   ├── alembic/                 # migrações Alembic
│   │   ├── scripts/                 # init_db.sh, seed_sentencas.py,
│   │   │                            # seed_mock_metrics.py, test_*.py
│   │   ├── tests/                   # testes (unit + integration)
│   │   ├── policy.yaml              # parâmetros da política de acordos
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   ├── front/                       # React 19 + TypeScript + Vite
│   │   ├── src/
│   │   │   ├── screens/             # Login, Home, Upload (Central de
│   │   │   │                        # Evidências), ProcessList (Mesa de
│   │   │   │                        # Decisão), Dashboard (Decision Lab),
│   │   │   │                        # Monitoring
│   │   │   ├── modules/             # theme, ui (SideBar, Icon, ...)
│   │   │   └── api/                 # TanStack Query hooks + axios client
│   │   ├── package.json
│   │   └── Dockerfile
│   └── models/
│       └── RN1/                     # Rede neural PyTorch + dados e scripts de treino
├── models/
│   ├── litigation_model.pth         # pesos treinados da RN1 (montados no container)
│   └── final_llm/                   # módulo de referência standalone (GPT-4o-mini + pdfplumber)
├── data/
│   └── examples/                    # processos de exemplo para demo
├── docs/
│   ├── presentation.html            # apresentação final (abrir no browser)
│   ├── ARQUITETURA.md               # arquitetura técnica
│   ├── policy.md                    # política de acordos (documentação)
│   ├── adr/                         # Architecture Decision Records
│   ├── relatorio_hackathon.pdf      # relatório escrito
│   └── README.md
├── ARCHITECTURE.md                  # overview de arquitetura (raiz)
├── DEVELOPMENT_CONTEXT.md           # contexto de desenvolvimento
├── SETUP.md                         # instruções detalhadas de setup
├── setup.sh                         # instalador auxiliar de dependências
├── .env.example
└── docker-compose.yml
```

---

## Documentos Suportados

| Código interno | Tipo | Descrição |
|----------------|------|-----------|
| `PETICAO_INICIAL` | Autos | Petição inicial do processo |
| `PROCURACAO` | Autos | Procuração do advogado do autor |
| `CONTRATO` | Subsídio | Contrato de empréstimo firmado |
| `EXTRATO` | Subsídio | Extrato bancário da conta do autor |
| `COMPROVANTE_CREDITO` | Subsídio | Comprovante regulatório BACEN |
| `DOSSIE` | Subsídio | Dossiê de autenticidade de assinaturas |
| `DEMONSTRATIVO_DIVIDA` | Subsídio | Evolução mensal da dívida |
| `LAUDO_REFERENCIADO` | Subsídio | Laudo interno da operação de crédito |

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19, TypeScript, Vite, TanStack Query, React Router v7, Zod |
| Backend | FastAPI 0.115, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Banco de dados | PostgreSQL 16 + pgvector |
| IA Generativa | OpenAI GPT-4o-mini (Structured Outputs) + `text-embedding-3-small` |
| ML | PyTorch (RN1), scikit-learn |
| OCR | Tesseract `por` + pdfplumber |
| Infraestrutura | Docker Compose, Ubuntu 24.04 |

---

## Apresentação

Abra `docs/presentation.html` diretamente no browser. Navegue com as setas ← → do teclado.

---

## Equipe — Grupo 10

Eduardo Muniz · Gabriel Rabelo · Gabriel Violante · Ian Paleta · Rafael Sollino
