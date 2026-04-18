"""Classificador RN1 — wrapper do modelo PyTorch para predição de derrota do banco."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Configurable via env — avaliação lazy para não explodir em Docker (parents[5] não existe)
def _resolve_rn1_dir() -> Path:
    if p := os.environ.get("RN1_DIR"):
        return Path(p)
    here = Path(__file__).resolve()
    # Repositório local: src/back/app/services/ai/classifier.py → 5 níveis até a raiz
    try:
        return here.parents[5] / "src" / "models" / "RN1"
    except IndexError:
        return Path("/rn1")


def _resolve_model_path() -> Path:
    if p := os.environ.get("RN1_MODEL_PATH"):
        return Path(p)
    here = Path(__file__).resolve()
    try:
        return here.parents[5] / "models" / "litigation_model.pth"
    except IndexError:
        return Path("/rn1_models/litigation_model.pth")


_RN1_DIR = _resolve_rn1_dir()
_MODEL_PATH = _resolve_model_path()

# Mapping from DB doc_type → RN1 feature name
_DOC_TYPE_TO_FEATURE: dict[str, str] = {
    "CONTRATO": "Contrato",
    "EXTRATO": "Extrato",
    "COMPROVANTE_CREDITO": "Comprovante de crédito",
    "DOSSIE": "Dossiê",
    "DEMONSTRATIVO_DIVIDA": "Demonstrativo de evolução da dívida",
    "LAUDO_REFERENCIADO": "Laudo referenciado",
}

_predictor = None


def _load_predictor():
    """Lazy-load do singleton LitigationPredictor do módulo RN1."""
    global _predictor
    if _predictor is not None:
        return _predictor

    for p in (str(_RN1_DIR), str(_RN1_DIR / "training")):
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        import torch
        from RN1 import LitigationPredictor  # type: ignore[import]

        _predictor = LitigationPredictor()

        # Sobrescreve os pesos com o caminho configurado via env (necessário no Docker)
        if _MODEL_PATH.exists():
            _predictor.model.load_state_dict(
                torch.load(str(_MODEL_PATH), map_location="cpu", weights_only=True)
            )
            _predictor.model.eval()
            logger.info("Pesos RN1 carregados de %s", _MODEL_PATH)
        else:
            logger.warning("Pesos RN1 não encontrados em %s — usando pesos internos", _MODEL_PATH)

        logger.info("Modelo RN1 inicializado de %s", _RN1_DIR)
    except Exception as exc:
        logger.error("Falha ao inicializar RN1: %s", exc)
        raise RuntimeError(f"Falha ao inicializar classificador RN1: {exc}") from exc

    return _predictor


def predict_outcome(processo_metadata: dict[str, Any]) -> float:
    """Prediz a probabilidade de derrota do banco para um processo.

    Args:
        processo_metadata: Dict com UF, Sub-assunto, Valor da causa e flags de subsídios.

    Returns:
        Float em [0, 1] representando probabilidade de derrota (Não Êxito).
    """
    predictor = _load_predictor()
    result = predictor.predict(processo_metadata)
    return float(result["probabilidade_perda"])


def build_case_data(
    uf: str | None,
    sub_assunto: str | None,
    valor_causa: float | None,
    doc_types: list[str],
) -> dict[str, Any]:
    """Monta o dict de entrada do RN1 a partir dos metadados do processo."""
    doc_flags = {feat: 0.0 for feat in _DOC_TYPE_TO_FEATURE.values()}
    for dt in doc_types:
        feat = _DOC_TYPE_TO_FEATURE.get(dt)
        if feat:
            doc_flags[feat] = 1.0

    return {
        "UF": uf or "SP",
        "Sub-assunto": sub_assunto or "generico",
        "Valor da causa": float(valor_causa or 0.0),
        **doc_flags,
    }
