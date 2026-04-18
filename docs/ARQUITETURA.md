# Arquitetura Técnica — Grupo 10

Este documento descreve a estrutura técnica e o fluxo de dados da solução desenvolvida para o Banco UFMG.

## Visão Geral

A solução é composta por três camadas principais:

1.  **Backend (FastAPI)**: Gerencia a persistência, autenticação e orquestração dos serviços de IA.
2.  **Frontend (React + Vite)**: Interface rica para advogados aprovarem acordos e para o banco monitorar métricas de efetividade.
3.  **Módulo de Inteligência Artificial (OpenAI)**: O "cérebro" da operação, responsável pela leitura de PDFs e tomada de decisão estratégica.

## Fluxo de Processamento (Pipeline IA)

O processamento de um novo processo segue o fluxo:

1.  **Ingestão**: O PDF é recebido e processado pelo `pdfplumber`. Caso seja um PDF escaneado (imagem), o sistema aciona automaticamente o `Tesseract OCR`.
2.  **Extração**: O GPT-4o-mini extrai dados estruturados (valor da causa, número do processo) e identifica a presença de documentos críticos (Contrato, Comprovante BACEN).
3.  **Classificação (Regra de Decisão)**: A IA cruza os documentos presentes com a jurisprudência interna para decidir entre **DEFESA** (Ganho provável) ou **ACORDO** (Dificuldade de defesa).
4.  **Valoração**: Se a decisão for ACORDO, o sistema calcula uma proposta otimizada baseada na política do banco (30-70% da causa) e no custo evitado de uma condenação média.

## Stack Tecnológica

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL, Alembic.
- **Frontend**: TypeScript, React, Vite, CSS moderno (Vanilla).
- **IA/ML**: OpenAI SDK (gpt-4o-mini, text-embedding-3-small), pgvector (para RAG futuro).
- **Dados**: Pandas, Openpyxl (para ingestão de bases históricas).

## Infraestrutura e Segurança

- **Containerização**: Docker e Docker Compose para fácil deploy e consistência de ambiente.
- **Segurança**: Autenticação via JWT, separação de papéis (Advogado vs Banco) e proteção de chaves de API via variáveis de ambiente/secrets.
- **Persistência**: PostgreSQL com extensão `pgvector` para buscas semânticas em sentenças históricas.

## Monitoramento (Efetividade e Aderência)

O sistema registra cada decisão tomada pela IA e a decisão final do advogado. Isso permite o cálculo de:
- **Aderência**: % de vezes que o advogado seguiu a recomendação da IA.
- **Efetividade**: Economia real gerada (Valor de condenação evitado - Valor de acordo pago).
