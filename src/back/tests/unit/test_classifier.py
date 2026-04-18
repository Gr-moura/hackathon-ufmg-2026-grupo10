"""Unit tests para `app.services.ai.llm_classifier`.

Cobre:
  - Fallback para None quando não há OPENAI_API_KEY
  - Resiliência a exceções da SDK OpenAI
  - Normalização de caixa (ACORDO/DEFESA)
  - Rejeição de decisão inválida
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.ai.llm_classifier import (
    ClassifierInput,
    ClassifierOutput,
    _format_user_message,
    classify,
)


def _mk_input(**overrides) -> ClassifierInput:
    defaults = dict(
        uf="MG",
        sub_assunto="golpe",
        valor_causa=10_000.0,
        doc_types_presentes=["PETICAO_INICIAL", "EXTRATO"],
        fatores_pro_acordo=["peticao_inicial_ingerida"],
        fatores_pro_defesa=["contrato_ausente"],
        penalty_documental=-0.20,
        probabilidade_vitoria_historica=0.22,
        casos_similares=[{"n_amostras": 150, "uf": "MG", "win_rate": 0.22}],
        trechos_peticao=["A parte autora alega ter sido vítima de golpe…"],
    )
    defaults.update(overrides)
    return ClassifierInput(**defaults)


@patch("app.services.ai.llm_classifier.get_settings")
def test_classifier_sem_api_key_retorna_none(mock_settings):
    mock_settings.return_value.openai_api_key = None
    out = classify(_mk_input())
    assert out is None


@patch("app.services.ai.llm_classifier.get_settings")
def test_classifier_falha_sdk_retorna_none(mock_settings):
    mock_settings.return_value.openai_api_key = "sk-fake"
    mock_settings.return_value.openai_model_reasoning = "gpt-4o-mini"

    with patch("openai.OpenAI", side_effect=RuntimeError("rede")):
        out = classify(_mk_input())
    assert out is None


@patch("app.services.ai.llm_classifier.get_settings")
def test_classifier_normaliza_decisao_lowercase(mock_settings):
    mock_settings.return_value.openai_api_key = "sk-fake"
    mock_settings.return_value.openai_model_reasoning = "gpt-4o-mini"

    parsed = ClassifierOutput(
        decisao="acordo",
        confidence=0.75,
        rationale="ok",
        fatores_extra_pro_acordo=[],
        fatores_extra_pro_defesa=[],
    )
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))]
    )

    fake_client = MagicMock()
    fake_client.beta.chat.completions.parse.return_value = fake_response

    with patch("openai.OpenAI", return_value=fake_client):
        out = classify(_mk_input())

    assert out is not None
    assert out.decisao == "ACORDO"


@patch("app.services.ai.llm_classifier.get_settings")
def test_classifier_rejeita_decisao_invalida(mock_settings):
    mock_settings.return_value.openai_api_key = "sk-fake"
    mock_settings.return_value.openai_model_reasoning = "gpt-4o-mini"

    parsed = ClassifierOutput(
        decisao="TALVEZ",
        confidence=0.5,
        rationale="indecisão",
    )
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))]
    )
    fake_client = MagicMock()
    fake_client.beta.chat.completions.parse.return_value = fake_response

    with patch("openai.OpenAI", return_value=fake_client):
        out = classify(_mk_input())

    assert out is None


def test_format_user_message_sem_valor_causa_nao_crasha():
    inp = _mk_input(valor_causa=None)
    msg = _format_user_message(inp)
    assert "Valor da causa: não identificado" in msg
    assert "UF: MG" in msg


def test_format_user_message_inclui_casos_similares():
    inp = _mk_input()
    msg = _format_user_message(inp)
    assert "CASOS SIMILARES" in msg
    assert "win_rate" in msg or "n_amostras" in msg


def test_format_user_message_com_valor():
    inp = _mk_input(valor_causa=12_345.67)
    msg = _format_user_message(inp)
    assert "R$ 12345.67" in msg
