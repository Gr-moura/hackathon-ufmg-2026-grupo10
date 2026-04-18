# Arquitetura do EnterOS

Documento de referência técnica completo para o sistema EnterOS — pipeline de IA para política de acordos jurídicos.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Diagrama de Componentes](#2-diagrama-de-componentes)
3. [Backend — FastAPI](#3-backend--fastapi)
4. [Pipeline de IA](#4-pipeline-de-ia)
5. [Modelo RN1 — Rede Neural](#5-modelo-rn1--rede-neural)
6. [Banco de Dados](#6-banco-de-dados)
7. [Frontend — React](#7-frontend--react)
8. [Infraestrutura](#8-infraestrutura)
9. [Segurança e Autenticação](#9-segurança-e-autenticação)
10. [Política de Acordos (policy.yaml)](#10-política-de-acordos-policyyaml)
11. [Fluxo de Dados Completo](#11-fluxo-de-dados-completo)

---

## 1. Visão Geral

O EnterOS é composto por três camadas principais:

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React 19 + TypeScript)                           │
│  Evidence Hub · Decision Lab · Monitoring · Process List    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/JSON (axios + JWT)
┌──────────────────────────▼──────────────────────────────────┐
│  Backend (FastAPI + Python 3.12)                            │
│  Routers: auth · processes · analysis · metrics             │
│  Services: AI Pipeline · Ingestion · Metrics Aggregator     │
└──────┬──────────────────────────────────────┬───────────────┘
       │ SQLAlchemy 2.0                        │ OpenAI API
┌──────▼───────────────┐         ┌────────────▼──────────────┐
│  PostgreSQL 16       │         │  GPT-4o-mini              │
│  + pgvector          │         │  text-embedding-3-small   │
│  6 tabelas + 60k     │         │  Structured Outputs       │
│  sentenças vetori-   │         │  (Pydantic)               │
│  zadas               │         └───────────────────────────┘
└──────────────────────┘
```

---

## 2. Diagrama de Componentes

```
src/
├── back/app/
│   ├── main.py              ← FastAPI app, CORS, startup
│   ├── config.py            ← Settings (env vars via Pydantic BaseSettings)
│   ├── deps.py              ← OAuth2 token validation, DB session injection
│   ├── core/
│   │   ├── security.py      ← JWT encode/decode, mock user store
│   │   ├── exceptions.py    ← DocumentParsingError
│   │   └── logging.py       ← structlog setup
│   ├── db/
│   │   ├── base.py          ← SQLAlchemy DeclarativeBase
│   │   ├── session.py       ← SessionLocal factory
│   │   └── models/
│   │       ├── processo.py           ← Processo (case)
│   │       ├── documento.py          ← Documento (PDF)
│   │       ├── analise_ia.py         ← AnaliseIA (AI output)
│   │       ├── decisao_advogado.py   ← DecisaoAdvogado (HITL)
│   │       ├── proposta_acordo.py    ← PropostaAcordo (value)
│   │       └── sentenca_historica.py ← SentencaHistorica (60k)
│   ├── routers/
│   │   ├── auth.py          ← POST /auth/login
│   │   ├── processes.py     ← POST/GET /processes
│   │   ├── analysis.py      ← POST /analyze, GET /analysis, POST /decision
│   │   └── metrics.py       ← GET /dashboard/metrics, /recommendations
│   ├── schemas/
│   │   ├── process.py       ← ProcessoResponse, DocumentoResponse
│   │   └── analysis.py      ← AnaliseIAResponse, PropostaAcordoResponse
│   └── services/
│       ├── ai/
│       │   ├── pipeline.py       ← run_pipeline() — orquestra os 5 estágios
│       │   ├── extractor.py      ← extract_metadata() — GPT Structured Outputs
│       │   ├── retriever.py      ← InProcessRetriever — RAG com pgvector
│       │   ├── classifier.py     ← LitigationPredictor — wrapper RN1 PyTorch
│       │   ├── llm_classifier.py ← classify() — GPT ACORDO/DEFESA
│       │   └── valuator.py       ← evaluate_settlement() — GPT + policy.yaml
│       ├── ingestion/
│       │   ├── pdf.py        ← ingest_pdf() — pdfplumber + OCR fallback
│       │   ├── ocr.py        ← pytesseract pt-BR
│       │   └── xlsx.py       ← load_sentencas() — carrega CSV histórico
│       └── metrics/
│           └── aggregator.py ← get_global_metrics(), get_recommendations_feed()
```

---

## 3. Backend — FastAPI

### 3.1 Configuração (`app/config.py`)

Classe `Settings` via `pydantic-settings`, lida do `.env`:

| Variável | Default | Descrição |
|----------|---------|-----------|
| `openai_api_key` | — | Chave OpenAI |
| `openai_model_reasoning` | `gpt-4o-mini` | Modelo para classificação e valoração |
| `openai_model_embedding` | `text-embedding-3-small` | Modelo para embeddings RAG |
| `database_url` | — | URL SQLAlchemy PostgreSQL |
| `jwt_secret` | `secret-dev` | Segredo JWT |
| `jwt_algorithm` | `HS256` | Algoritmo JWT |
| `jwt_expire_minutes` | `480` | Validade do token (8h) |
| `data_dir` | `/data` | Diretório para PDFs em disco |
| `log_level` | `INFO` | Nível de log |

### 3.2 Rotas da API

#### `POST /auth/login`
Autenticação OAuth2. Retorna JWT com `role` (`advogado` ou `banco`).

```
Request:  application/x-www-form-urlencoded { username, password }
Response: { access_token, token_type: "bearer", role, name }
```

Usuários hardcoded (demo):
- `advogado@banco.com` / `advogado123` → role `advogado`
- `banco@banco.com` / `banco123` → role `banco`

---

#### `POST /processes`
Cria processo e ingere PDFs.

```
Request:  multipart/form-data {
  numero_processo: str,
  valor_causa?: float,
  files: File[]   ← PDFs (múltiplos)
}
Response: ProcessoResponse (201)
```

**Fluxo interno:**
1. Cria registro `Processo` no banco
2. Para cada PDF: chama `ingest_pdf()` → grava `Documento` com `raw_text`
3. Chama `extract_metadata(combined_text)` → grava `metadata_extraida` no `Processo`
4. Retorna `ProcessoResponse` com documentos

---

#### `GET /processes`
Lista processos do advogado autenticado (filtrado por `advogado_id`).

---

#### `GET /processes/{processo_id}`
Retorna processo com todos os documentos associados.

---

#### `POST /processes/{processo_id}/analyze`
Executa o pipeline de IA completo.

```
Response: AnaliseIAResponse {
  id, processo_id,
  decisao: "ACORDO" | "DEFESA",
  confidence: float,
  rationale: str,
  fatores_pro_acordo: str[],
  fatores_pro_defesa: str[],
  requires_supervisor: bool,
  trechos_chave: [{doc, page, quote}],
  proposta?: {
    valor_sugerido, intervalo_min, intervalo_max,
    custo_estimado_litigar, economia_esperada,
    n_casos_similares
  }
}
```

---

#### `GET /processes/{processo_id}/analysis`
Retorna análise já executada (cache do banco).

---

#### `POST /processes/analysis/{analise_id}/decision`
Registra decisão do advogado (HITL).

```
Request: {
  acao: "ACEITAR" | "AJUSTAR" | "RECUSAR",
  valor_advogado?: float,   ← obrigatório se acao=AJUSTAR
  justificativa?: str       ← obrigatório se delta > 15%
}
Response: 204 No Content
```

**Validações:**
- Se `acao = AJUSTAR` e delta percentual > 15%: `justificativa` é obrigatória
- Se delta > 30%: log de warning para auditoria
- Atualiza `Processo.status = "concluido"`

---

#### `GET /dashboard/metrics`
Métricas consolidadas para o painel do banco.

```
Response: {
  total_processos: int,
  total_decisoes: int,
  aderencia_global: float,           ← aceitos / total_decisoes
  economia_total: float,             ← Σ(custo_litigar - valor_advogado)
  casos_alto_risco: int,             ← confidence < 0.60
  aderencia_por_advogado: [{
    advogado_id, total, aceitos, aderencia
  }],
  drift_confianca: [{                ← últimos 7 dias
    dia: date, avg_confidence: float
  }]
}
```

---

#### `GET /dashboard/recommendations`
Feed das últimas 20 recomendações (ordenadas por data desc).

---

## 4. Pipeline de IA

Orquestrado por `run_pipeline(processo_id, db)` em `services/ai/pipeline.py`.  
Executa 5 estágios em sequência. Cada estágio tem fallback para garantir disponibilidade mesmo sem API key.

### Estágio 1 — Extração de Metadados

**Arquivo:** `services/ai/extractor.py`  
**Função:** `extract_metadata(text: str) → ProcessMetadata`

Usa GPT-4o-mini com **Structured Outputs** (Pydantic) para extrair:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `uf` | `str \| None` | Sigla do estado (ex: MG, SP) |
| `valor_da_causa` | `float \| None` | Valor da causa em reais (sem R$) |
| `sub_assunto` | `"golpe" \| "generico" \| None` | Classificação do tipo de caso |

**Regras do prompt:**
- `golpe`: evidência clara de fraude de terceiro — "nunca contratei", "minha identidade foi usada", "falsificação de documentos"
- `generico`: não reconhecimento sem prova de fraude — esquecimento, cobrança indevida, contrato contestado

**Cache:** se `processo.metadata_extraida` já existe, pula esta etapa.  
**Truncamento:** texto limitado a 32.000 tokens, com prioridade à petição inicial.

---

### Estágio 2 — RAG (Retrieval-Augmented Generation)

**Arquivo:** `services/ai/retriever.py`  
**Classe:** `InProcessRetriever`

**Funcionamento:**
1. Divide cada documento em chunks de ~400 palavras com overlap de 50 palavras
2. Gera embeddings via `text-embedding-3-small` (OpenAI, 1 chamada batch)
3. Para cada tópico de busca, calcula similaridade coseno e retorna top-3 chunks

**Tópicos buscados:**

| Tópico | Objetivo |
|--------|----------|
| `assinatura` | Cláusulas de autenticidade de assinatura |
| `valor_operacao` | Valor do empréstimo, taxa, prazo |
| `provas_banco` | Evidências do banco (contrato, extrato, comprovante) |
| `fraude` | Alegações de fraude ou envolvimento de terceiro |

**Fallback:** se OpenAI indisponível, usa overlap de palavras-chave (sem embeddings).  
**Custo estimado:** ~$0.001 por processo (7 PDFs, ~50 chunks).

---

### Estágio 3 — RN1 (Rede Neural de Risco)

**Arquivo:** `services/ai/classifier.py`  
**Classe:** `LitigationPredictor`

Wrapper em torno do modelo PyTorch treinado em 60.000 sentenças históricas.

**Input (features):**

| Feature | Tipo | Descrição |
|---------|------|-----------|
| `UF` | categorical (one-hot) | Estado do processo |
| `Sub-assunto` | categorical | golpe / nao_reconhece / revisional / generico |
| `Valor da causa` | float (normalizado) | Valor da causa em reais |
| `Contrato` | binary (0/1) | Subsídio presente |
| `Extrato` | binary (0/1) | Subsídio presente |
| `Comprovante de crédito` | binary (0/1) | Subsídio presente |
| `Dossiê` | binary (0/1) | Subsídio presente |
| `Demonstrativo de evolução da dívida` | binary (0/1) | Subsídio presente |
| `Laudo referenciado` | binary (0/1) | Subsídio presente |

**Output:**
- `prob_derrota`: probabilidade do banco perder a causa ∈ [0, 1]

**Fallback determinístico** (se modelo não carrega):
```python
prob_derrota = max(0.75 - num_docs_presentes * 0.10, 0.20)
```

---

### Estágio 4 — Classificador LLM (Decisão Qualitativa)

**Arquivo:** `services/ai/llm_classifier.py`  
**Função:** `classify(input: ClassifierInput) → ClassifierOutput | None`

**Input fornecido ao GPT:**

```python
ClassifierInput:
  uf: str
  sub_assunto: str
  valor_causa: float
  doc_types_presentes: list[str]
  fatores_pro_acordo: list[str]     ← análise dos documentos
  fatores_pro_defesa: list[str]
  probabilidade_vitoria_historica: float   ← 1 - prob_derrota (RN1)
  casos_similares: {                       ← histórico agregado
    n_amostras, uf, sub_assunto, win_rate
  }
  trechos_peticao: list[str]              ← top-3 excerpts do RAG
```

**Output Structured:**

```python
ClassifierOutput:
  decisao: "ACORDO" | "DEFESA"
  confidence: float          ← [0, 1]
  rationale: str             ← ≤ 600 caracteres
  fatores_extra_pro_acordo: list[str]
  fatores_extra_pro_defesa: list[str]
```

**Fallback** (sem API key):
```python
decisao = "ACORDO" if prob_derrota > 0.60 else "DEFESA"
confidence = prob_derrota if ACORDO else 1 - prob_derrota
```

---

### Estágio 5 — Valuator (Cálculo do Valor de Acordo)

**Arquivo:** `services/ai/valuator.py`  
**Função:** `evaluate_settlement(ctx: ValuationContext) → ValuationResult`

Ativado **somente se** `decisao == "ACORDO"`.

**Parâmetros da `policy.yaml` injetados no prompt:**

```yaml
piso_pct_valor_causa: 0.30      # Oferta mínima = 30% do valor da causa
teto_pct_valor_causa: 0.70      # Oferta máxima = 70% do valor da causa
piso_absoluto_brl: 1500         # Piso absoluto em BRL
teto_absoluto_brl: 50000        # Teto absoluto em BRL
```

**Output:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `valor_sugerido` | float | Oferta de abertura (BRL) |
| `intervalo_max` | float | Teto de negociação (BRL) |
| `custo_estimado_litigar` | float | Custo total estimado se litigar |
| `justificativa` | str | Raciocínio matemático + documental |

**Intervalos persistidos em `PropostaAcordo`:**
- `intervalo_min` = 30% do valor da causa (piso da policy)
- `intervalo_max` = min(75% custo_litigar, 70% valor_causa)
- `economia_esperada` = custo_litigar − valor_sugerido

---

### Estágio Final — Persistência

1. Polimento do `rationale` via GPT (português jurídico, 2 parágrafos, sem jargão de ML)
2. Extração dos 5 principais `trechos_chave` dos chunks RAG
3. Gravação de `AnaliseIA` + `PropostaAcordo` (se ACORDO)
4. Atualização de `Processo.status = "analisado"`

---

## 5. Modelo RN1 — Rede Neural

**Localização:** `src/models/RN1/`  
**Pesos treinados:** `models/litigation_model.pth`

### Arquitetura (`training/model.py`)

```
LitigationModel(nn.Module):
  Input:  vetor de features (dim varia com UF one-hot, ~30-50 features)
  Layer 1: Linear(input_dim → 128) + ReLU + Dropout(0.3)
  Layer 2: Linear(128 → 64) + ReLU + Dropout(0.3)
  Layer 3: Linear(64 → 32) + ReLU
  Output:  Linear(32 → 2) + Softmax
           Classe 0: banco ganha | Classe 1: banco perde
```

### Dataset (`training/dataset.py`)

Classe `LitigationDataset`:
- Carrega `resultados_dos_processos.csv` + `subsidios_disponibilizados.csv`
- Merge por número de processo
- Encoding: `LabelEncoder` para UF e sub-assunto
- Scaling: `StandardScaler` para valor da causa
- Target: binário (0 = Êxito/Improcedência, 1 = Derrota/Procedência/Acordo)

### Treinamento (`training/train.py`)

```
Otimizador: Adam (lr=0.001)
Loss:       CrossEntropyLoss
Epochs:     50
Batch size: 64
Split:      80% treino / 20% validação
```

---

## 6. Banco de Dados

### Schema

```sql
-- Processo (caso jurídico)
CREATE TABLE processo (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  numero_processo   TEXT NOT NULL,
  advogado_id       TEXT NOT NULL,
  valor_causa       NUMERIC(12,2),
  status            TEXT DEFAULT 'pendente',   -- pendente | processando | analisado | concluido
  metadata_extraida JSONB,                      -- {uf, sub_assunto, valor_da_causa}
  created_at        TIMESTAMP DEFAULT now()
);

-- Documento (PDF ingested)
CREATE TABLE documento (
  id                UUID PRIMARY KEY,
  processo_id       UUID REFERENCES processo(id),
  doc_type          TEXT,           -- PETICAO_INICIAL, CONTRATO, EXTRATO, etc.
  original_filename TEXT,
  storage_path      TEXT,           -- caminho em disco
  raw_text          TEXT,           -- texto extraído
  tables            JSONB,          -- tabelas detectadas
  page_count        INT,
  parse_errors      JSONB           -- [{stage, reason, recoverable}]
);

-- AnaliseIA (output do pipeline)
CREATE TABLE analise_ia (
  id                    UUID PRIMARY KEY,
  processo_id           UUID REFERENCES processo(id) UNIQUE,
  decisao               TEXT,       -- ACORDO | DEFESA
  confidence            FLOAT,
  rationale             TEXT,
  fatores_pro_acordo    JSONB,      -- [str]
  fatores_pro_defesa    JSONB,      -- [str]
  requires_supervisor   BOOLEAN,    -- true se confidence < 0.85
  variaveis_extraidas   JSONB,      -- features RN1 + prob_derrota
  casos_similares       JSONB,      -- estatísticas do histórico
  trechos_chave         JSONB,      -- [{doc, page, quote}]
  created_at            TIMESTAMP
);

-- PropostaAcordo (apenas se decisao=ACORDO)
CREATE TABLE proposta_acordo (
  id                       UUID PRIMARY KEY,
  analise_id               UUID REFERENCES analise_ia(id) UNIQUE,
  valor_sugerido           NUMERIC,
  valor_base_estatistico   NUMERIC,
  modulador_llm            FLOAT,
  intervalo_min            NUMERIC,
  intervalo_max            NUMERIC,
  custo_estimado_litigar   NUMERIC,
  n_casos_similares        INT
);

-- DecisaoAdvogado (HITL)
CREATE TABLE decisao_advogado (
  id              UUID PRIMARY KEY,
  analise_id      UUID REFERENCES analise_ia(id) UNIQUE,
  acao            TEXT,       -- ACEITAR | AJUSTAR | RECUSAR
  valor_advogado  NUMERIC,
  justificativa   TEXT,
  advogado_id     TEXT,
  created_at      TIMESTAMP
);

-- SentencaHistorica (60.000 registros históricos)
CREATE TABLE sentenca_historica (
  id               BIGSERIAL PRIMARY KEY,
  numero_caso      TEXT,
  uf               TEXT,
  assunto          TEXT,
  sub_assunto      TEXT,
  resultado_macro  TEXT,       -- Êxito | Derrota | Acordo
  resultado_micro  TEXT,       -- Improcedência | Procedência | etc.
  valor_causa      NUMERIC,
  valor_condenacao NUMERIC,
  embedding        VECTOR(1536)  -- pgvector: text-embedding-3-small
);
```

### Índices Relevantes

```sql
CREATE INDEX ON processo(advogado_id);
CREATE INDEX ON processo(status);
CREATE INDEX ON documento(processo_id);
CREATE INDEX ON sentenca_historica(uf);
CREATE INDEX ON sentenca_historica(sub_assunto);
CREATE INDEX ON sentenca_historica USING ivfflat (embedding vector_cosine_ops);
```

---

## 7. Frontend — React

### Telas

| Rota | Componente | Acesso | Descrição |
|------|-----------|--------|-----------|
| `/` | `Home` | Público | Redirect baseado em role |
| `/login` | `LoginScreen` | Público | Autenticação OAuth2 |
| `/upload` | `UploadScreen` (Evidence Hub) | advogado | Upload sequencial de 7 documentos |
| `/dashboard/:id` | `DashboardScreen` (Decision Lab) | advogado | Recomendação + HITL |
| `/monitoring` | `MonitoringScreen` | banco | Dashboard executivo |
| `/processes` | `ProcessListScreen` | advogado | Lista de casos |

### Camada de API (`src/api/`)

**`client.ts`**: axios com interceptor que injeta `Authorization: Bearer {token}` e redireciona para `/login` em 401.

**Hooks TanStack Query (`processes.ts`):**

```typescript
useLogin()                       // POST /auth/login
useUploadProcesso()              // POST /processes (multipart)
useProcessos()                   // GET /processes
useProcesso(processoId)          // GET /processes/:id
useAnalysis(processoId)          // GET /processes/:id/analysis
useAnalyzeProcesso()             // POST /processes/:id/analyze
useRegisterDecision()            // POST /processes/analysis/:id/decision
```

**Hooks de métricas (`metrics.ts`):**

```typescript
useMetrics()                     // GET /dashboard/metrics
useRecommendations()             // GET /dashboard/recommendations
```

### Evidence Hub (UploadScreen)

Fluxo sequencial guiado pelos 7 documentos obrigatórios:

1. Interface exibe documento atual a ser enviado
2. Usuário seleciona PDF (drag & drop ou clique)
3. Pode pular com "mark as missing" — documento fica com status `missing`
4. Ao completar a sequência, botão "Upload and Analyze" dispara `POST /processes`
5. Barra de progresso: 0% → 30% (upload) → 60% (análise) → 100% → redirect ao Dashboard

**Tipos de status por documento:**

| Status | Descrição |
|--------|-----------|
| `pending` | Aguardando arquivo |
| `selected` | Arquivo selecionado, aguardando envio final |
| `uploaded` | Enviado com sucesso |
| `missing` | Marcado como ausente pelo advogado |

### Decision Lab (DashboardScreen)

Estados da tela em função da query:

| Condição | UI exibida |
|----------|-----------|
| `!processoId` | Tela de boas-vindas com botões de navegação |
| `isLoading` | Spinner "Carregando análise…" |
| `isError \|\| !analysis` | Botão "Executar análise de IA" |
| `analysis` disponível | Recomendação completa + `LawyerDecisionPanel` |

**Auto-trigger:** se a análise retorna 404 (não executada ainda), o `useEffect` dispara `analyze.mutate()` automaticamente.

**`LawyerDecisionPanel`:**
- Seletor ACEITAR / AJUSTAR / RECUSAR
- Se AJUSTAR: campo de valor numérico com cálculo de delta em tempo real
- Se delta > 15%: aviso e campo de justificativa obrigatório
- Formulário com validação client-side antes do `POST /decision`

---

## 8. Infraestrutura

### Docker Compose

```yaml
services:
  db:
    image: pgvector/pgvector:pg16      # PostgreSQL 16 + extensão vector
    ports: ["5432:5432"]
    healthcheck: pg_isready -U enteros

  back:
    build: ./src/back (Ubuntu 24.04)
    depends_on: db (healthcheck)
    entrypoint: scripts/init_db.sh     # espera DB + pgvector + alembic upgrade head
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ports: ["8000:8000"]
    volumes: ["./data:/data"]          # PDFs persistidos em disco

  front:
    build: ./src/front
    depends_on: [back]
    command: npm run dev -- --host 0.0.0.0
    ports: ["5173:5173"]
```

### Dockerfile do Backend (Ubuntu 24.04)

1. `FROM ubuntu:24.04` — base Linux
2. Instala: curl, gcc, libpq-dev, tesseract-ocr (pt-BR), python3.12, python3.12-venv
3. Node 18 via NodeSource
4. Cria virtualenv em `/opt/venv`
5. Instala todas as dependências pinadas (pip freeze)
6. Instala Playwright + Chromium
7. `COPY pyproject.toml` → `pip install .[dev]`
8. `COPY .` → reinstala para registrar scripts
9. `ENTRYPOINT: /bin/bash scripts/init_db.sh`

### `scripts/init_db.sh`

```bash
# 1. Aguarda PostgreSQL com PGPASSWORD
until psql -h db -U enteros -c '\q'; do sleep 1; done

# 2. Habilita pgvector
psql -h db -U enteros -d enteros -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 3. Executa o comando passado ao container (alembic + uvicorn)
exec "$@"
```

---

## 9. Segurança e Autenticação

- **JWT** com algoritmo HS256, expiração 8h
- **OAuth2PasswordBearer** — token extraído do header `Authorization: Bearer {token}`
- **Dependency Injection** via `deps.py`:
  - `get_current_user()`: valida token, retorna payload com `sub` (email) e `role`
  - `get_db()`: sessão SQLAlchemy por request
- **Role-based access**: rotas de métricas requerem `role=banco` (verificado no handler)
- **CORS**: configurado para aceitar qualquer origem em desenvolvimento (ajustar para produção)

---

## 10. Política de Acordos (`policy.yaml`)

Arquivo lido em runtime pelo Valuator. Define os limites da proposta de acordo:

```yaml
# Limites percentuais do valor da causa
piso_pct_valor_causa: 0.30     # Oferta mínima = 30% do valor da causa
teto_pct_valor_causa: 0.70     # Oferta máxima = 70% do valor da causa

# Limites absolutos em BRL
piso_absoluto_brl: 1500        # Nunca ofertar abaixo de R$ 1.500
teto_absoluto_brl: 50000       # Nunca ofertar acima de R$ 50.000

# Thresholds de confiança
confidence_thresholds:
  green: 0.85                  # Confiança alta — sem revisão supervisora
  yellow: 0.60                 # Confiança média — requer revisão

# requires_supervisor = confidence < 0.85
```

**Como o Valuator usa:**
1. Injeta os parâmetros no system prompt do GPT
2. GPT calcula `valor_sugerido` respeitando piso/teto
3. `intervalo_min` = 30% × valor_causa
4. `intervalo_max` = min(75% × custo_litigar, 70% × valor_causa)

---

## 11. Fluxo de Dados Completo

```
ADVOGADO faz upload dos PDFs
         │
         ▼
POST /processes (multipart/form-data)
         │
         ├─► Para cada PDF:
         │     ingest_pdf()
         │       ├─► pdfplumber → texto nativo
         │       └─► pytesseract (fallback OCR) → texto escaneado
         │     Grava Documento (raw_text, page_count, doc_type)
         │
         ├─► extract_metadata(combined_text)
         │     └─► GPT-4o-mini Structured Outputs
         │           → {uf, sub_assunto, valor_da_causa}
         │     Grava Processo.metadata_extraida
         │
         └─► Retorna ProcessoResponse ──► Frontend redireciona para /dashboard/:id

FRONTEND chama POST /processes/:id/analyze (auto ou botão)
         │
         ▼
run_pipeline(processo_id, db)
         │
         ├─► Estágio 1: extract_metadata() (usa cache se já existe)
         │
         ├─► Estágio 2: InProcessRetriever.from_documents()
         │     ├─► Chunking (400 palavras, overlap 50)
         │     ├─► text-embedding-3-small → embeddings
         │     └─► Busca coseno por tópico → trechos_chave[]
         │
         ├─► Estágio 3: LitigationPredictor.predict()
         │     ├─► Encode features (UF, sub_assunto, valor, doc flags)
         │     ├─► Forward pass LitigationModel (PyTorch)
         │     └─► prob_derrota ∈ [0, 1]
         │
         ├─► Estágio 4: llm_classifier.classify()
         │     ├─► Input: features + RN1 prob + RAG excerpts + histórico
         │     ├─► GPT-4o-mini Structured Outputs
         │     └─► {decisao, confidence, rationale, fatores}
         │
         ├─► Estágio 5 (se ACORDO): valuator.evaluate_settlement()
         │     ├─► Input: valor_causa + prob + sub_assunto + policy.yaml
         │     ├─► GPT-4o-mini Structured Outputs
         │     └─► {valor_sugerido, intervalo_max, custo_litigar, justificativa}
         │
         ├─► Polimento do rationale (GPT → português jurídico)
         ├─► Grava AnaliseIA + PropostaAcordo
         └─► Retorna AnaliseIAResponse

FRONTEND exibe Decision Lab
         │
         ├─► Mostra: decisão, confidence, rationale, fatores, trechos, proposta
         └─► LawyerDecisionPanel: ACEITAR / AJUSTAR / RECUSAR

ADVOGADO decide
         │
         ▼
POST /processes/analysis/:id/decision
         ├─► Valida delta percentual
         ├─► Exige justificativa se delta > 15%
         ├─► Grava DecisaoAdvogado
         └─► Atualiza Processo.status = "concluido"

BANCO acessa /monitoring
         │
         ▼
GET /dashboard/metrics
         ├─► aderencia_global = aceitos / total_decisoes
         ├─► economia_total = Σ(custo_litigar - valor_advogado)
         ├─► casos_alto_risco = count(confidence < 0.60)
         ├─► aderencia_por_advogado (breakdown individual)
         └─► drift_confianca (média diária dos últimos 7 dias)
```
