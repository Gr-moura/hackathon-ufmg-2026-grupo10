#!/usr/bin/env bash
# =============================================================================
# setup.sh — EnterOS: Política de Acordos Inteligente
# Instala dependências, configura o ambiente e sobe todos os serviços.
# Uso: bash setup.sh [--no-build] [--down]
# =============================================================================

set -euo pipefail

# ── Cores ────────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; RESET=''
fi

info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
step()    { echo -e "\n${BOLD}━━ $* ${RESET}"; }

# ── Argumentos ───────────────────────────────────────────────────────────────
NO_BUILD=false
TEARDOWN=false
for arg in "$@"; do
  case $arg in
    --no-build) NO_BUILD=true ;;
    --down)     TEARDOWN=true ;;
    --help|-h)
      echo "Uso: bash setup.sh [--no-build] [--down]"
      echo "  --no-build  Sobe os serviços sem reconstruir as imagens"
      echo "  --down      Para e remove todos os containers e volumes"
      exit 0
      ;;
  esac
done

# ── Banner ───────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║   EnterOS — Política de Acordos           ║"
echo "  ║   Hackathon UFMG 2026 · Grupo 10          ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${RESET}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# ── Teardown ─────────────────────────────────────────────────────────────────
if $TEARDOWN; then
  step "Removendo containers e volumes"
  docker compose down -v
  success "Ambiente removido."
  exit 0
fi

# ── 1. Pré-requisitos ─────────────────────────────────────────────────────────
step "1. Verificando pré-requisitos"

check_cmd() {
  local cmd=$1 label=$2 hint=$3
  if command -v "$cmd" &>/dev/null; then
    success "$label encontrado: $($cmd --version 2>&1 | head -1)"
  else
    error "$label não encontrado. $hint"
    exit 1
  fi
}

check_cmd docker      "Docker"         "Instale em https://docs.docker.com/get-docker/"
check_cmd git         "Git"            "Instale em https://git-scm.com/"

# Docker Compose (plugin v2 ou binário standalone)
if docker compose version &>/dev/null; then
  success "Docker Compose encontrado: $(docker compose version 2>&1 | head -1)"
elif command -v docker-compose &>/dev/null; then
  warn "docker-compose standalone detectado. Recomenda-se Docker Compose v2 (plugin)."
else
  error "Docker Compose não encontrado. Instale em https://docs.docker.com/compose/install/"
  exit 1
fi

# Docker daemon rodando?
if ! docker info &>/dev/null; then
  error "O daemon do Docker não está em execução. Inicie o Docker e tente novamente."
  exit 1
fi
success "Docker daemon está rodando."

# ── 2. Arquivo .env ──────────────────────────────────────────────────────────
step "2. Configurando variáveis de ambiente"

if [[ -f ".env" ]]; then
  success ".env já existe — mantendo configuração atual."
else
  if [[ -f ".env.example" ]]; then
    cp .env.example .env
    info ".env criado a partir de .env.example."
  else
    error ".env.example não encontrado. Certifique-se de estar na raiz do repositório."
    exit 1
  fi
fi

# Verifica se a chave OpenAI está configurada
OPENAI_KEY=$(grep -E "^OPENAI_API_KEY=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" || true)

if [[ -z "$OPENAI_KEY" || "$OPENAI_KEY" == "sk-..." || "$OPENAI_KEY" =~ ^sk-\.\.\. ]]; then
  echo ""
  warn "OPENAI_API_KEY não está configurada no arquivo .env."
  echo -n "  → Cole sua chave OpenAI agora (ou pressione ENTER para pular): "
  read -r user_key
  if [[ -n "$user_key" ]]; then
    # Substitui ou adiciona a chave
    if grep -q "^OPENAI_API_KEY=" .env; then
      sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=${user_key}|" .env
    else
      echo "OPENAI_API_KEY=${user_key}" >> .env
    fi
    success "OPENAI_API_KEY configurada."
  else
    warn "Sem chave OpenAI — extração de metadados e GPT Acordo não funcionarão."
    warn "O pipeline RN1 (offline) continuará disponível com fallback heurístico."
  fi
else
  success "OPENAI_API_KEY detectada no .env."
fi

# ── 3. Arquivos críticos do modelo ───────────────────────────────────────────
step "3. Verificando arquivos do modelo RN1"

MODEL_PTH="models/litigation_model.pth"
RN1_CSV_DIR="src/models/RN1/training"

if [[ -f "$MODEL_PTH" ]]; then
  MODEL_SIZE=$(du -sh "$MODEL_PTH" | cut -f1)
  success "Pesos do modelo encontrados: $MODEL_PTH ($MODEL_SIZE)"
else
  warn "Arquivo $MODEL_PTH não encontrado."
  warn "O classificador RN1 usará fallback heurístico baseado em subsídios presentes."
fi

if [[ -f "$RN1_CSV_DIR/resultados_dos_processos.csv" ]]; then
  success "Dataset de treino encontrado: $RN1_CSV_DIR/"
else
  warn "Dataset RN1 não encontrado em $RN1_CSV_DIR/. O classificador pode falhar."
fi

# ── 4. Dados de exemplo ───────────────────────────────────────────────────────
step "4. Verificando dados de exemplo"

if [[ -d "data/processos_exemplo" ]]; then
  N_PROCESSOS=$(find data/processos_exemplo -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
  success "Processos de exemplo encontrados: $N_PROCESSOS processo(s) em data/processos_exemplo/"
else
  warn "Pasta data/processos_exemplo/ não encontrada."
  warn "Coloque os PDFs de exemplo da banca para testar o caminho dourado."
fi

# ── 5. Build e inicialização ──────────────────────────────────────────────────
step "5. Construindo e iniciando os serviços Docker"

if $NO_BUILD; then
  info "Flag --no-build ativa — pulando rebuild das imagens."
  docker compose up -d
else
  info "Isso pode demorar 5–10 minutos na primeira vez (download do PyTorch CPU ~200MB)."
  docker compose up --build -d
fi

# ── 6. Aguarda os serviços ficarem prontos ────────────────────────────────────
step "6. Aguardando os serviços ficarem prontos"

TIMEOUT=120
ELAPSED=0

info "Aguardando o backend (porta 8000)..."
until curl -sf "http://localhost:8000/health" &>/dev/null; do
  if [[ $ELAPSED -ge $TIMEOUT ]]; then
    error "Timeout: o backend não respondeu em ${TIMEOUT}s."
    echo ""
    echo "  Verifique os logs com: docker compose logs back"
    exit 1
  fi
  sleep 3
  ELAPSED=$((ELAPSED + 3))
  echo -n "."
done
echo ""
success "Backend está respondendo (${ELAPSED}s)."

info "Aguardando o frontend (porta 5173)..."
ELAPSED=0
until curl -sf "http://localhost:5173" &>/dev/null; do
  if [[ $ELAPSED -ge $TIMEOUT ]]; then
    warn "Frontend não respondeu em ${TIMEOUT}s — pode ainda estar compilando."
    break
  fi
  sleep 3
  ELAPSED=$((ELAPSED + 3))
  echo -n "."
done
echo ""
if curl -sf "http://localhost:5173" &>/dev/null; then
  success "Frontend está respondendo."
fi

# ── 7. Resultado final ────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN}  Ambiente pronto!${RESET}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════════${RESET}"
echo ""
echo -e "  ${BOLD}Frontend${RESET}   →  http://localhost:5173"
echo -e "  ${BOLD}API docs${RESET}   →  http://localhost:8000/docs"
echo -e "  ${BOLD}Health${RESET}     →  http://localhost:8000/health"
echo ""
echo -e "  ${BOLD}Credenciais de demo:${RESET}"
echo -e "  Advogado  →  advogado@banco.com  /  advogado123"
echo -e "  Banco     →  banco@banco.com     /  banco123"
echo ""
echo -e "  ${BOLD}Comandos úteis:${RESET}"
echo -e "  Logs do backend   →  docker compose logs -f back"
echo -e "  Parar tudo        →  docker compose down"
echo -e "  Resetar banco     →  bash setup.sh --down && bash setup.sh"
echo ""
