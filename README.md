# EnterOS — Política de Acordos Inteligente

> Solução desenvolvida pelo **Grupo 10** para o Hackathon UFMG 2026 (cliente: Banco UFMG).  
> Automatiza e monitora decisões de acordo/defesa em casos de não reconhecimento de contratação de empréstimo.

---

## O Problema

O Banco UFMG recebe ~5.000 processos/mês onde clientes alegam não reconhecer a contratação de um empréstimo. Para cada processo, um advogado externo decide: **propor acordo** ou **ir à defesa**. Sem ferramenta, essa decisão é subjetiva, lenta e impossível de monitorar em escala.

## Nossa Solução

O **EnterOS** é um sistema que:

1. Recebe os documentos do processo (Autos + Subsídios) via upload guiado
2. Executa um pipeline de IA que analisa os documentos e emite recomendação fundamentada
3. Apresenta ao advogado: decisão (ACORDO/DEFESA), valor sugerido, confiança e citações dos documentos
4. Registra a decisão do advogado para monitoramento de aderência e efetividade

---

## Requisitos Atendidos

| Requisito | Como é atendido |
|-----------|----------------|
| **Regra de decisão** | Pipeline: RN1 (PyTorch, 60k sentenças históricas) + GPT-4o-mini com Structured Outputs |
| **Sugestão de valor** | Valuator GPT calcula `valor_sugerido`, `intervalo_min/max` e `economia_esperada` com base na `policy.yaml` |
| **Acesso à recomendação** | Decision Lab (frontend React) com recomendação, confiança, trechos citados e fatores pró/contra |
| **Monitoramento de aderência** | Toda decisão do advogado é gravada com delta percentual, justificativa obrigatória se delta > 15% e timestamp |
| **Monitoramento de efetividade** | Dashboard executivo com taxa de acordos, economia acumulada, drift de confiança e alertas por advogado |

---

## Credenciais de Acesso

| Perfil | E-mail | Senha |
|--------|--------|-------|
| Advogado | `advogado@banco.com` | `advogado123` |
| Banco (gestor) | `banco@banco.com` | `banco123` |

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

Edite `.env` e preencha:

```env
OPENAI_API_KEY=sk-...           # Chave da OpenAI
POSTGRES_PASSWORD=enteros_dev   # Senha do PostgreSQL (pode manter)
DATABASE_URL=postgresql+psycopg://enteros:enteros_dev@db:5432/enteros
DATA_DIR=/data
```

### 3. Suba os containers

```bash
docker compose up --build
```

O `init_db.sh` aguarda o banco subir, habilita a extensão `pgvector` e executa as migrações Alembic automaticamente.

### 4. Acesse

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend (Swagger) | http://localhost:8000/docs |
| PostgreSQL | `localhost:5432` (usuário: `enteros`) |

---

## Rodando Localmente (sem Docker)

### Pré-requisitos

- Python 3.12+
- Node.js 18+
- PostgreSQL 16 com extensão `pgvector`

### Backend

```bash
cd src/back

# Crie e ative o virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install -e ".[dev]"

# Configure o banco
createdb enteros
psql -d enteros -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Crie o .env local
cat > .env << EOF
DATABASE_URL=postgresql+psycopg://seu_usuario:sua_senha@localhost:5432/enteros
OPENAI_API_KEY=sk-...
DATA_DIR=/tmp/enteros-data
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

1. **Login** com `advogado@banco.com`
2. **Evidence Hub** (`/upload`): upload sequencial dos 7 documentos do processo — a interface guia documento a documento, permitindo pular com "mark as missing"
3. **Decision Lab** (`/dashboard/:id`): visualiza a recomendação da IA — decisão, nível de confiança, valor sugerido com intervalo, fatores pró-acordo e pró-defesa, trechos citados dos documentos
4. **HITL**: aceita, ajusta (com justificativa obrigatória se delta > 15%) ou recusa a recomendação

### Perfil: Banco (Gestor)

1. **Login** com `banco@banco.com`
2. **Monitoring** (`/monitoring`): acompanha métricas globais — total de processos, aderência por advogado, economia acumulada vs. condenações, casos de alto risco (confiança < 60%) e feed das últimas recomendações

---

## Estrutura do Projeto

```
hackathon-ufmg-2026-grupo10/
├── src/
│   ├── back/                    # API FastAPI (Python 3.12)
│   │   ├── app/
│   │   │   ├── main.py          # App + CORS + routers
│   │   │   ├── config.py        # Settings via Pydantic BaseSettings
│   │   │   ├── deps.py          # OAuth2 + SQLAlchemy session DI
│   │   │   ├── core/            # security (JWT), logging, exceptions
│   │   │   ├── db/models/       # processo, documento, analise_ia,
│   │   │   │                    # decisao_advogado, proposta_acordo,
│   │   │   │                    # sentenca_historica
│   │   │   ├── routers/         # auth, processes, analysis, metrics
│   │   │   ├── schemas/         # Pydantic request/response models
│   │   │   └── services/
│   │   │       ├── ai/          # pipeline, extractor, classifier,
│   │   │       │                # valuator, llm_classifier, retriever
│   │   │       ├── ingestion/   # pdf, ocr, xlsx
│   │   │       └── metrics/     # aggregator
│   │   ├── alembic/             # Migrações de banco de dados
│   │   ├── policy.yaml          # Parâmetros da política de acordos
│   │   └── Dockerfile
│   ├── front/                   # React 19 + TypeScript + Vite
│   │   └── src/
│   │       ├── screens/         # Login, Upload (Evidence Hub),
│   │       │                    # Dashboard (Decision Lab),
│   │       │                    # Monitoring, ProcessList
│   │       └── api/             # TanStack Query hooks + axios client
│   ├── models/
│   │   └── RN1/                 # Rede neural PyTorch + treinamento
│   └── scraper/                 # Coleta DataJud CNJ (auxiliar)
├── models/
│   └── litigation_model.pth     # Pesos treinados da RN1
├── data/
│   └── examples/                # Processos de exemplo para demo
├── docs/
│   └── presentation.html        # Apresentação final (abrir no browser)
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
| Frontend | React 19, TypeScript, Vite, TanStack Query |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Banco de dados | PostgreSQL 16 + pgvector |
| IA Generativa | OpenAI GPT-4o-mini (Structured Outputs + embeddings) |
| ML | PyTorch (RN1), XGBoost |
| OCR | Tesseract pt-BR + pdfplumber |
| Infraestrutura | Docker Compose, Ubuntu 24.04 |

---

## Apresentação

Abra `docs/presentation.html` diretamente no browser. Navegue com as setas ← → do teclado.

---

## Equipe — Grupo 10

Eduardo Muniz · Gabriel Rabelo · Gabriel Violante · Ian Paleta · Rafael Sollino
