"""
Suíte de testes de integração — Caminho Dourado do EnterOS.

Valida que o Frontend (TanStack Query hooks) e o Backend (FastAPI routers)
estão usando o mesmo contrato de dados definido em §6 do DEVELOPMENT_CONTEXT.md.

Cenários:
  1. Autenticação  — login com sucesso, JWT retornado, erro 401
  2. Ingestão      — upload multipart de PDF, persistência no banco
  3. HITL          — ACEITAR/AJUSTAR/RECUSAR; status do processo → "concluido"
  4. Consistência  — schema de /dashboard/metrics bate com MetricsResponse do TS

⚠️  DISCREPÂNCIAS IDENTIFICADAS (§6.2 × types.ts):

  [D1] RESOLVIDO: PropostaAcordoResponse agora usa float.
       Garante que o JSON retornado seja um `number` no TypeScript.

  [D2] RESOLVIDO: MetricsResponse agora usa submodels tipados.
       AderenciaAdvogado e DriftConfianca garantem a estrutura interna.

  [D3] O endpoint POST /processes/{id}/analyze retorna 501 (DEV-2 pendente).
       O hook useAnalyzeProcesso() chamará este endpoint — estamos testando
       a resposta 501 de forma explícita para documentar o estado atual.

Execução rápida:
  cd src/back && pytest tests/integration/ -v
"""

from __future__ import annotations

import decimal
import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.analise_ia import AnaliseIA
from app.db.models.decisao_advogado import DecisaoAdvogado
from app.db.models.processo import Processo
from app.db.models.proposta_acordo import PropostaAcordo
from tests.conftest import get_advogado_token, get_banco_token


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _minimal_pdf() -> bytes:
    """PDF mínimo válido de 1 página em branco."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type /Pages /Kids[3 0 R] /Count 1>>endobj\n"
        b"3 0 obj<</Type /Page /MediaBox[0 0 612 792] /Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer<</Size 4 /Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )


def _seed_analise_completa(
    db: Session,
    decisao: str = "ACORDO",
    confidence: float = 0.90,
) -> tuple[Processo, AnaliseIA, PropostaAcordo]:
    """Cria processo + análise IA + proposta de acordo direto no banco."""
    processo = Processo(
        numero_processo="0001111-11.2024.8.13.0001",
        advogado_id="00000000-0000-0000-0000-000000000001",
        valor_causa=10000.0,
        status="analisado",
    )
    db.add(processo)
    db.flush()

    analise = AnaliseIA(
        processo_id=processo.id,
        decisao=decisao,
        confidence=confidence,
        rationale="Análise de teste — similaridade alta com histórico.",
        fatores_pro_acordo=["pagamento_no_extrato", "dossie_presente"],
        fatores_pro_defesa=["valor_causa_elevado"],
        requires_supervisor=confidence < 0.60,
        trechos_chave=[{"doc": "peticao_inicial", "page": 1, "quote": "trecho relevante"}],
    )
    db.add(analise)
    db.flush()

    proposta = PropostaAcordo(
        analise_id=analise.id,
        valor_sugerido=decimal.Decimal("5000.00"),
        valor_base_estatistico=decimal.Decimal("5200.00"),
        modulador_llm=0.96,
        intervalo_min=decimal.Decimal("4000.00"),
        intervalo_max=decimal.Decimal("6500.00"),
        custo_estimado_litigar=decimal.Decimal("12000.00"),
        n_casos_similares=30,
    )
    db.add(proposta)
    db.commit()
    db.refresh(analise)

    return processo, analise, proposta


# ===========================================================================
# Cenário 1 — Autenticação
# ===========================================================================

class TestAutenticacao:
    """Valida o fluxo de login e proteção de rotas via JWT."""

    def test_login_advogado_retorna_token_e_role(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/login",
            data={"username": "advogado@banco.com", "password": "advogado123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["role"] == "advogado"
        assert body["name"] == "Dr. João Silva"

    def test_login_banco_retorna_role_correto(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/login",
            data={"username": "banco@banco.com", "password": "banco123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["role"] == "banco"
        assert "access_token" in body

    def test_login_senha_errada_retorna_401(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/login",
            data={"username": "advogado@banco.com", "password": "senha_errada"},
        )
        assert resp.status_code == 401

    def test_login_usuario_inexistente_retorna_401(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/login",
            data={"username": "fantasma@banco.com", "password": "qualquer"},
        )
        assert resp.status_code == 401

    def test_rota_protegida_sem_token_retorna_401(self, client: TestClient) -> None:
        # Simula frontend sem token no localStorage
        resp = client.get("/processes")
        assert resp.status_code == 401

    def test_rota_protegida_token_invalido_retorna_401(self, client: TestClient) -> None:
        resp = client.get(
            "/processes",
            headers={"Authorization": "Bearer eyJinvalido.payload.assinatura"},
        )
        assert resp.status_code == 401

    def test_token_valido_autoriza_acesso(self, client: TestClient) -> None:
        token = get_advogado_token(client)
        resp = client.get("/processes", headers=_auth(token))
        assert resp.status_code == 200

    def test_health_nao_requer_autenticacao(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ===========================================================================
# Cenário 2 — Ingestão de Processo (upload multipart)
# ===========================================================================

class TestIngestionProcesso:
    """Valida POST /processes com upload de documentos PDF."""

    @patch("app.routers.processes.ingest_pdf")
    @patch("app.routers.processes._storage_dir")
    def test_upload_com_pdf_retorna_201(
        self,
        mock_storage: MagicMock,
        mock_ingest: MagicMock,
        client: TestClient,
        tmp_path,
    ) -> None:
        mock_storage.return_value = tmp_path
        mock_ingest.return_value = MagicMock(
            raw_text="Texto da petição inicial extraído.",
            tables=[],
            page_count=3,
            doc_type="PETICAO_INICIAL",
            parse_errors=[],
        )

        token = get_advogado_token(client)
        resp = client.post(
            "/processes",
            headers=_auth(token),
            data={
                "numero_processo": "0001234-56.2024.8.13.0001",
                "valor_causa": "15000.00",
            },
            files=[("files", ("peticao_inicial.pdf", BytesIO(_minimal_pdf()), "application/pdf"))],
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["numero_processo"] == "0001234-56.2024.8.13.0001"
        assert body["status"] == "pendente"
        assert len(body["documentos"]) == 1
        doc = body["documentos"][0]
        assert doc["doc_type"] == "PETICAO_INICIAL"
        assert doc["original_filename"] == "peticao_inicial.pdf"
        assert doc["page_count"] == 3
        assert "id" in body

    @patch("app.routers.processes._storage_dir")
    def test_upload_sem_arquivos_cria_processo_vazio(
        self,
        mock_storage: MagicMock,
        client: TestClient,
        tmp_path,
    ) -> None:
        mock_storage.return_value = tmp_path
        token = get_advogado_token(client)
        resp = client.post(
            "/processes",
            headers=_auth(token),
            data={"numero_processo": "PROC-VAZIO-001"},
        )
        assert resp.status_code == 201
        assert resp.json()["documentos"] == []
        assert resp.json()["status"] == "pendente"

    def test_upload_sem_auth_retorna_401(self, client: TestClient) -> None:
        resp = client.post(
            "/processes",
            data={"numero_processo": "0001234-56.2024.8.13.0001"},
        )
        assert resp.status_code == 401

    @patch("app.routers.processes.ingest_pdf")
    @patch("app.routers.processes._storage_dir")
    def test_lista_processos_retorna_apenas_do_advogado(
        self,
        mock_storage: MagicMock,
        mock_ingest: MagicMock,
        client: TestClient,
        db: Session,
        tmp_path,
    ) -> None:
        """Isolamento por advogado_id — advogado não vê processos de terceiros."""
        mock_storage.return_value = tmp_path
        mock_ingest.return_value = MagicMock(
            raw_text="texto", tables=[], page_count=1, doc_type="OUTRO", parse_errors=[]
        )
        token = get_advogado_token(client)

        client.post(
            "/processes",
            headers=_auth(token),
            data={"numero_processo": "PROC-ADV-001"},
        )

        # Insere processo de outro advogado direto no banco
        outro = Processo(
            numero_processo="PROC-OUTRO-001",
            advogado_id="outro-advogado-id",
            status="pendente",
        )
        db.add(outro)
        db.commit()

        resp = client.get("/processes", headers=_auth(token))
        assert resp.status_code == 200
        numeros = [p["numero_processo"] for p in resp.json()]
        assert "PROC-ADV-001" in numeros
        assert "PROC-OUTRO-001" not in numeros

    @patch("app.routers.processes.ingest_pdf")
    @patch("app.routers.processes._storage_dir")
    def test_get_processo_por_id(
        self,
        mock_storage: MagicMock,
        mock_ingest: MagicMock,
        client: TestClient,
        tmp_path,
    ) -> None:
        mock_storage.return_value = tmp_path
        mock_ingest.return_value = MagicMock(
            raw_text="texto", tables=[], page_count=1, doc_type="OUTRO", parse_errors=[]
        )
        token = get_advogado_token(client)

        created = client.post(
            "/processes",
            headers=_auth(token),
            data={"numero_processo": "PROC-GET-001"},
        ).json()

        resp = client.get(f"/processes/{created['id']}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_processo_inexistente_retorna_404(self, client: TestClient) -> None:
        token = get_advogado_token(client)
        resp = client.get(f"/processes/{uuid.uuid4()}", headers=_auth(token))
        assert resp.status_code == 404

    def test_pipeline_ia_retorna_200_com_analise_persistida(
        self, client: TestClient, db: Session
    ) -> None:
        """Confirma que o endpoint de análise executa o pipeline determinístico e
        devolve AnaliseIAResponse persistida.
        """
        processo = Processo(
            numero_processo="PROC-ANALYZE-001",
            advogado_id="00000000-0000-0000-0000-000000000001",
            valor_causa=10000.0,
            status="pendente",
            metadata_extraida={"uf": "MG", "sub_assunto": "generico", "valor_da_causa": 10000.0},
        )
        db.add(processo)
        db.commit()

        token = get_advogado_token(client)
        resp = client.post(f"/processes/{processo.id}/analyze", headers=_auth(token))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["processo_id"] == str(processo.id)
        assert body["decisao"] in {"ACORDO", "DEFESA"}
        assert 0.0 <= body["confidence"] <= 1.0
        assert isinstance(body["rationale"], str) and body["rationale"]
        # Proposta só existe quando decisao == ACORDO
        if body["decisao"] == "ACORDO":
            assert body["proposta"] is not None
            assert body["proposta"]["valor_sugerido"] > 0

    def test_pipeline_ia_idempotente(
        self, client: TestClient, db: Session
    ) -> None:
        """Chamar analyze duas vezes no mesmo processo devolve a mesma análise."""
        processo = Processo(
            numero_processo="PROC-IDEMP-001",
            advogado_id="00000000-0000-0000-0000-000000000001",
            valor_causa=8000.0,
            status="pendente",
            metadata_extraida={"uf": "SP", "sub_assunto": "golpe", "valor_da_causa": 8000.0},
        )
        db.add(processo)
        db.commit()

        token = get_advogado_token(client)
        r1 = client.post(f"/processes/{processo.id}/analyze", headers=_auth(token))
        r2 = client.post(f"/processes/{processo.id}/analyze", headers=_auth(token))
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]

    def test_pipeline_preenche_trechos_chave_via_rag(
        self, client: TestClient, db: Session
    ) -> None:
        """Com documentos contendo `raw_text`, o RAG deve popular trechos_chave."""
        from app.db.models.documento import Documento

        processo = Processo(
            numero_processo="PROC-RAG-001",
            advogado_id="00000000-0000-0000-0000-000000000001",
            valor_causa=12000.0,
            status="pendente",
            metadata_extraida={
                "uf": "MG",
                "sub_assunto": "golpe",
                "valor_da_causa": 12000.0,
            },
        )
        db.add(processo)
        db.flush()

        db.add_all(
            [
                Documento(
                    processo_id=processo.id,
                    doc_type="PETICAO_INICIAL",
                    original_filename="peticao.pdf",
                    raw_text=(
                        "A parte autora alega que nunca contratou o empréstimo "
                        "e que houve golpe. Não reconhece a assinatura presente "
                        "no instrumento contratual apresentado pelo banco. "
                        "Sustenta ter sido vítima de fraude por terceiros."
                    ),
                ),
                Documento(
                    processo_id=processo.id,
                    doc_type="CONTRATO",
                    original_filename="contrato.pdf",
                    raw_text=(
                        "Contrato de empréstimo pessoal nº 1234 celebrado entre "
                        "as partes no valor de R$ 12.000,00 com prazo de 36 meses."
                    ),
                ),
            ]
        )
        db.commit()

        token = get_advogado_token(client)
        resp = client.post(
            f"/processes/{processo.id}/analyze", headers=_auth(token)
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # trechos_chave deve conter pelo menos 1 entrada baseada nos docs
        assert body["trechos_chave"], "RAG deveria ter populado trechos_chave"
        assert all("doc" in t and "quote" in t for t in body["trechos_chave"])
        # rationale deve mencionar o método RAG usado
        assert "RAG=" in body["rationale"]
        # Trechos chave devem vir dos docs fornecidos (doc_type esperado)
        doc_types = {t["doc"] for t in body["trechos_chave"]}
        assert doc_types <= {"PETICAO_INICIAL", "CONTRATO"}

        # variaveis_extraidas persiste na AnaliseIA (não é exposto pelo schema,
        # mas podemos verificar via DB diretamente).
        analise = (
            db.query(AnaliseIA)
            .filter(AnaliseIA.id == uuid.UUID(body["id"]))
            .one()
        )
        assert analise.variaveis_extraidas is not None
        assert "rag_method" in analise.variaveis_extraidas
        assert "probabilidade_vitoria_historica" in analise.variaveis_extraidas


# ===========================================================================
# Cenário 3 — HITL: Human-in-the-Loop (§4.5)
# ===========================================================================

class TestHITL:
    """Valida o fluxo de decisão do advogado: ACEITAR / AJUSTAR / RECUSAR."""

    def test_aceitar_retorna_204_e_muda_status_para_concluido(
        self, client: TestClient, db: Session
    ) -> None:
        token = get_advogado_token(client)
        processo, analise, _ = _seed_analise_completa(db)

        resp = client.post(
            f"/processes/analysis/{analise.id}/decision",
            headers=_auth(token),
            json={"acao": "ACEITAR"},
        )
        assert resp.status_code == 204

        db.refresh(processo)
        assert processo.status == "concluido"

    def test_aceitar_registra_decisao_correta_no_banco(
        self, client: TestClient, db: Session
    ) -> None:
        token = get_advogado_token(client)
        _, analise, _ = _seed_analise_completa(db)

        client.post(
            f"/processes/analysis/{analise.id}/decision",
            headers=_auth(token),
            json={"acao": "ACEITAR"},
        )

        decisao = db.query(DecisaoAdvogado).filter(
            DecisaoAdvogado.analise_id == analise.id
        ).first()
        assert decisao is not None
        assert decisao.acao == "ACEITAR"
        assert decisao.advogado_id == "00000000-0000-0000-0000-000000000001"

    def test_ajustar_delta_pequeno_sem_justificativa_aceito(
        self, client: TestClient, db: Session
    ) -> None:
        """Delta ≤ 15% não exige justificativa (§4.5)."""
        token = get_advogado_token(client)
        _, analise, _ = _seed_analise_completa(db)

        # valor_sugerido = 5000, proposta 5100 = 2% de delta
        resp = client.post(
            f"/processes/analysis/{analise.id}/decision",
            headers=_auth(token),
            json={"acao": "AJUSTAR", "valor_advogado": 5100.0},
        )
        assert resp.status_code == 204

    def test_ajustar_delta_grande_sem_justificativa_retorna_422(
        self, client: TestClient, db: Session
    ) -> None:
        """Delta > 15% sem justificativa deve falhar com 422 (§4.5)."""
        token = get_advogado_token(client)
        _, analise, _ = _seed_analise_completa(db)

        # valor_sugerido = 5000, proposta 2000 = 60% de delta
        resp = client.post(
            f"/processes/analysis/{analise.id}/decision",
            headers=_auth(token),
            json={"acao": "AJUSTAR", "valor_advogado": 2000.0},
        )
        assert resp.status_code == 422

    def test_ajustar_delta_grande_com_justificativa_aceito(
        self, client: TestClient, db: Session
    ) -> None:
        """Delta > 15% COM justificativa deve ser aceito (§4.5)."""
        token = get_advogado_token(client)
        _, analise, _ = _seed_analise_completa(db)

        resp = client.post(
            f"/processes/analysis/{analise.id}/decision",
            headers=_auth(token),
            json={
                "acao": "AJUSTAR",
                "valor_advogado": 2000.0,
                "justificativa": "Cliente demonstrou vulnerabilidade financeira comprovada.",
            },
        )
        assert resp.status_code == 204

    def test_recusar_registra_defesa(
        self, client: TestClient, db: Session
    ) -> None:
        token = get_advogado_token(client)
        processo, analise, _ = _seed_analise_completa(db)

        resp = client.post(
            f"/processes/analysis/{analise.id}/decision",
            headers=_auth(token),
            json={"acao": "RECUSAR", "justificativa": "Documentação inconsistente."},
        )
        assert resp.status_code == 204

        decisao = db.query(DecisaoAdvogado).filter(
            DecisaoAdvogado.analise_id == analise.id
        ).first()
        assert decisao is not None
        assert decisao.acao == "RECUSAR"

        db.refresh(processo)
        assert processo.status == "concluido"

    def test_decision_analise_inexistente_retorna_404(
        self, client: TestClient
    ) -> None:
        token = get_advogado_token(client)
        resp = client.post(
            f"/processes/analysis/{uuid.uuid4()}/decision",
            headers=_auth(token),
            json={"acao": "ACEITAR"},
        )
        assert resp.status_code == 404

    def test_upsert_decision_sobrescreve_anterior(
        self, client: TestClient, db: Session
    ) -> None:
        """Segunda chamada ao endpoint deve sobrescrever a decisão existente."""
        token = get_advogado_token(client)
        _, analise, _ = _seed_analise_completa(db)

        client.post(
            f"/processes/analysis/{analise.id}/decision",
            headers=_auth(token),
            json={"acao": "ACEITAR"},
        )
        client.post(
            f"/processes/analysis/{analise.id}/decision",
            headers=_auth(token),
            json={"acao": "RECUSAR", "justificativa": "Revisão após análise adicional."},
        )

        total = db.query(DecisaoAdvogado).filter(
            DecisaoAdvogado.analise_id == analise.id
        ).count()
        assert total == 1  # Não deve duplicar

        decisao = db.query(DecisaoAdvogado).filter(
            DecisaoAdvogado.analise_id == analise.id
        ).first()
        assert decisao is not None
        assert decisao.acao == "RECUSAR"

    def test_get_analysis_retorna_schema_analise_ia_response(
        self, client: TestClient, db: Session
    ) -> None:
        """Valida que GET /processes/{id}/analysis retorna AnaliseIAResponse §6.2."""
        token = get_advogado_token(client)
        processo, _, _ = _seed_analise_completa(db)

        resp = client.get(
            f"/processes/{processo.id}/analysis",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()

        # Campos obrigatórios conforme AnaliseIAResponse (§6.2)
        assert "id" in body
        assert "processo_id" in body
        assert body["decisao"] in ("ACORDO", "DEFESA")
        assert isinstance(body["confidence"], float)
        assert 0.0 <= body["confidence"] <= 1.0
        assert isinstance(body["rationale"], str)
        assert isinstance(body["fatores_pro_acordo"], list)
        assert isinstance(body["fatores_pro_defesa"], list)
        assert isinstance(body["requires_supervisor"], bool)
        assert isinstance(body["trechos_chave"], list)

        # PropostaAcordoResponse presente para ACORDO
        proposta = body["proposta"]
        assert proposta is not None
        assert "valor_sugerido" in proposta
        assert "intervalo_min" in proposta
        assert "intervalo_max" in proposta
        assert "custo_estimado_litigar" in proposta
        assert "economia_esperada" in proposta
        assert "n_casos_similares" in proposta

        # [D1] economia_esperada deve ser >= 0 (regra do _to_response)
        assert float(proposta["economia_esperada"]) >= 0.0

        # [D1] FIX APLICADO: Agora usamos float no schema Pydantic.
        # O assert abaixo valida que o JSON retornado contém um número, não uma string.
        assert isinstance(proposta["valor_sugerido"], (float, int))

    def test_get_analysis_inexistente_retorna_404(
        self, client: TestClient, db: Session
    ) -> None:
        processo = Processo(
            numero_processo="PROC-SEM-ANALISE",
            advogado_id="00000000-0000-0000-0000-000000000001",
            status="pendente",
        )
        db.add(processo)
        db.commit()

        token = get_advogado_token(client)
        resp = client.get(
            f"/processes/{processo.id}/analysis",
            headers=_auth(token),
        )
        assert resp.status_code == 404


# ===========================================================================
# Cenário 4 — Consistência de Dados: /dashboard/metrics (§4.6)
# ===========================================================================

class TestMetricsConsistencia:
    """
    Valida que o schema retornado por GET /dashboard/metrics é exatamente
    o que MonitoringScreen.tsx e MetricsResponse (types.ts) esperam.
    """

    def _seed_metricas(self, db: Session) -> None:
        """Popula banco com 1 processo analisado + decisão ACEITAR."""
        processo = Processo(
            numero_processo="PROC-METRICAS-001",
            advogado_id="00000000-0000-0000-0000-000000000001",
            valor_causa=20000.0,
            status="concluido",
        )
        db.add(processo)
        db.flush()

        analise = AnaliseIA(
            processo_id=processo.id,
            decisao="ACORDO",
            confidence=0.88,
            rationale="Alta similaridade com histórico de casos.",
            fatores_pro_acordo=["pagamento_no_extrato"],
            fatores_pro_defesa=[],
            requires_supervisor=False,
            trechos_chave=[],
        )
        db.add(analise)
        db.flush()

        proposta = PropostaAcordo(
            analise_id=analise.id,
            valor_sugerido=decimal.Decimal("8000.00"),
            valor_base_estatistico=decimal.Decimal("8500.00"),
            modulador_llm=0.94,
            intervalo_min=decimal.Decimal("6000.00"),
            intervalo_max=decimal.Decimal("10000.00"),
            custo_estimado_litigar=decimal.Decimal("18000.00"),
            n_casos_similares=45,
        )
        db.add(proposta)
        db.flush()

        decisao = DecisaoAdvogado(
            analise_id=analise.id,
            acao="ACEITAR",
            valor_advogado=decimal.Decimal("8000.00"),
            advogado_id="00000000-0000-0000-0000-000000000001",
        )
        db.add(decisao)
        db.commit()

    def test_schema_completo_bate_com_interface_typescript(
        self, client: TestClient, db: Session
    ) -> None:
        """
        Garante que todos os campos de MetricsResponse (types.ts) estão presentes
        na resposta de GET /dashboard/metrics. Se um campo mudar no back, este
        teste quebra e alerta o time.
        """
        token = get_banco_token(client)
        resp = client.get("/dashboard/metrics", headers=_auth(token))

        assert resp.status_code == 200
        body = resp.json()

        # Campos exatos da interface TypeScript MetricsResponse
        assert "total_processos" in body
        assert "total_decisoes" in body
        assert "aderencia_global" in body
        assert "economia_total" in body
        assert "casos_alto_risco" in body
        assert "aderencia_por_advogado" in body
        assert "drift_confianca" in body

        # Tipos primitivos
        assert isinstance(body["total_processos"], int)
        assert isinstance(body["total_decisoes"], int)
        assert isinstance(body["casos_alto_risco"], int)
        assert isinstance(body["aderencia_por_advogado"], list)
        assert isinstance(body["drift_confianca"], list)

    def test_banco_vazio_retorna_nulls_esperados(
        self, client: TestClient
    ) -> None:
        """Com DB vazio, MonitoringScreen deve receber nulls (e renderizar '—')."""
        token = get_banco_token(client)
        resp = client.get("/dashboard/metrics", headers=_auth(token))

        body = resp.json()
        assert body["aderencia_global"] is None    # null no TypeScript
        assert body["economia_total"] is None      # null no TypeScript
        assert body["total_processos"] == 0
        assert body["total_decisoes"] == 0
        assert body["casos_alto_risco"] == 0
        assert body["aderencia_por_advogado"] == []
        assert isinstance(body["drift_confianca"], list)

    def test_aderencia_global_com_um_aceitar(
        self, client: TestClient, db: Session
    ) -> None:
        """1 ACEITAR de 1 decisão = aderência global de 1.0 (100%)."""
        self._seed_metricas(db)
        token = get_banco_token(client)

        body = client.get("/dashboard/metrics", headers=_auth(token)).json()

        assert body["total_processos"] >= 1
        assert body["total_decisoes"] >= 1
        assert body["aderencia_global"] == 1.0

    def test_aderencia_por_advogado_tem_campos_corretos(
        self, client: TestClient, db: Session
    ) -> None:
        """
        [D2] Valida o shape de aderencia_por_advogado contra a interface TS:
          Array<{ advogado_id: string; total: number; aceitos: number; aderencia: number }>
        """
        self._seed_metricas(db)
        token = get_banco_token(client)

        body = client.get("/dashboard/metrics", headers=_auth(token)).json()

        assert len(body["aderencia_por_advogado"]) >= 1
        for item in body["aderencia_por_advogado"]:
            assert "advogado_id" in item, "[D2] campo advogado_id ausente"
            assert "total" in item, "[D2] campo total ausente"
            assert "aceitos" in item, "[D2] campo aceitos ausente"
            assert "aderencia" in item, "[D2] campo aderencia ausente"
            assert isinstance(item["advogado_id"], str)
            assert isinstance(item["total"], int)
            assert isinstance(item["aceitos"], int)
            assert isinstance(item["aderencia"], float)
            assert 0.0 <= item["aderencia"] <= 1.0

    def test_recommendations_feed_bate_com_recommendation_feed_item(
        self, client: TestClient, db: Session
    ) -> None:
        """
        Valida que GET /dashboard/recommendations retorna lista de
        RecommendationFeedItem conforme definido em types.ts.
        """
        self._seed_metricas(db)
        token = get_banco_token(client)

        resp = client.get("/dashboard/recommendations", headers=_auth(token))
        assert resp.status_code == 200

        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 1

        for item in items:
            assert "processo_id" in item
            assert "numero_processo" in item
            assert "decisao" in item
            assert "confidence" in item
            assert "valor_sugerido" in item
            assert "created_at" in item
            assert item["decisao"] in ("ACORDO", "DEFESA")
            assert isinstance(item["confidence"], float)
            assert 0.0 <= item["confidence"] <= 1.0
            # valor_sugerido: float | null
            assert item["valor_sugerido"] is None or isinstance(item["valor_sugerido"], (int, float))
            # created_at deve ser ISO 8601
            assert "T" in item["created_at"] or item["created_at"].count("-") >= 2

    def test_metrics_requer_autenticacao(self, client: TestClient) -> None:
        resp = client.get("/dashboard/metrics")
        assert resp.status_code == 401

    def test_recommendations_requer_autenticacao(self, client: TestClient) -> None:
        resp = client.get("/dashboard/recommendations")
        assert resp.status_code == 401
