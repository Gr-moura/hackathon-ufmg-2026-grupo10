"""RAG retriever — chunking + kNN sobre os PDFs do **processo corrente**.

Uso correto: ground classifier/valuator com trechos específicos das petições
e subsídios daquele processo, não com casos históricos externos.

Fluxo:
    1. `InProcessRetriever.from_documents(docs)` — particiona cada `Documento`
       em chunks de ~500 tokens (window) com 50 tokens de sobreposição.
    2. Embedda todos os chunks em 1 chamada de `text-embedding-3-small`.
    3. `.search(question, k=3)` — embedda a pergunta e devolve os top-k
       chunks por similaridade de cosseno, em memória (NumPy).

Projetado para ser **stateless**: criado a cada `run_pipeline`, descartado ao
final. Não persiste nada. Sem `OPENAI_API_KEY`, cai para BM25-esque naive
keyword overlap — mantém o pipeline funcionando em modo offline.

Custo típico por processo (7 PDFs, ~50 chunks): < $0.001.
"""
from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_CHUNK_WORDS = 400  # ≈ 500 tokens
_CHUNK_OVERLAP = 50
_MIN_CHUNK_CHARS = 40


@dataclass
class Chunk:
    doc_type: str
    doc_filename: str
    chunk_index: int
    text: str
    embedding: list[float] | None = None

    def preview(self, max_chars: int = 240) -> str:
        t = self.text.strip().replace("\n", " ")
        return t if len(t) <= max_chars else t[: max_chars - 1] + "…"


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float  # maior = mais similar (cosine similarity)


@dataclass
class InProcessRetriever:
    chunks: list[Chunk] = field(default_factory=list)
    _method: str = "naive"  # "embedding" | "naive"

    @classmethod
    def from_documents(cls, documents: Sequence[object]) -> InProcessRetriever:
        """Constrói retriever a partir de uma lista de `Documento` SQLAlchemy.

        Aceita qualquer objeto com `raw_text`, `doc_type`, `original_filename`.
        """
        chunks: list[Chunk] = []
        for doc in documents:
            raw = getattr(doc, "raw_text", None) or ""
            if not raw.strip():
                continue
            for idx, piece in enumerate(_window_chunks(raw)):
                if len(piece) < _MIN_CHUNK_CHARS:
                    continue
                chunks.append(
                    Chunk(
                        doc_type=getattr(doc, "doc_type", "OUTRO"),
                        doc_filename=getattr(doc, "original_filename", "doc.pdf"),
                        chunk_index=idx,
                        text=piece,
                    )
                )

        retriever = cls(chunks=chunks)
        retriever._embed_all()
        return retriever

    def _embed_all(self) -> None:
        """Popula `.embedding` de cada chunk via OpenAI (1 chamada em batch)."""
        if not self.chunks:
            return
        settings = get_settings()
        if not settings.openai_api_key:
            logger.info(
                "Retriever: sem OPENAI_API_KEY — usando keyword overlap naive"
            )
            self._method = "naive"
            return
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            texts = [c.text for c in self.chunks]
            resp = client.embeddings.create(
                model=settings.openai_model_embedding,
                input=texts,
            )
            for c, item in zip(self.chunks, resp.data, strict=False):
                c.embedding = item.embedding
            self._method = "embedding"
            logger.info("Retriever: %d chunks embedados", len(self.chunks))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Retriever: falha ao gerar embeddings (%s) — fallback naive",
                exc,
            )
            self._method = "naive"

    def search(self, question: str, k: int = 3) -> list[RetrievedChunk]:
        """kNN por cosseno (ou keyword overlap em fallback)."""
        if not self.chunks:
            return []
        if self._method == "embedding":
            q_vec = self._embed_question(question)
            if q_vec is None:
                return self._naive_search(question, k)
            scored = [
                RetrievedChunk(chunk=c, score=_cosine(q_vec, c.embedding or []))
                for c in self.chunks
                if c.embedding
            ]
        else:
            return self._naive_search(question, k)

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]

    def _embed_question(self, question: str) -> list[float] | None:
        try:
            from openai import OpenAI

            settings = get_settings()
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.embeddings.create(
                model=settings.openai_model_embedding, input=question
            )
            return resp.data[0].embedding
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao embeddar pergunta: %s", exc)
            return None

    def _naive_search(self, question: str, k: int) -> list[RetrievedChunk]:
        """Fallback sem embeddings — pontua por interseção de tokens."""
        q_tokens = {
            t.lower() for t in re.findall(r"\w{4,}", question) if len(t) >= 4
        }
        if not q_tokens:
            return []
        scored: list[RetrievedChunk] = []
        for c in self.chunks:
            c_tokens = {t.lower() for t in re.findall(r"\w{4,}", c.text)}
            overlap = len(q_tokens & c_tokens)
            if overlap:
                scored.append(
                    RetrievedChunk(
                        chunk=c,
                        score=overlap / max(len(q_tokens), 1),
                    )
                )
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]

    @property
    def method(self) -> str:
        return self._method


def _window_chunks(text: str) -> Iterable[str]:
    """Particiona texto em janelas de ~400 palavras com overlap de 50."""
    # Normaliza espaços e quebras
    words = re.split(r"\s+", text.strip())
    if not words:
        return
    step = _CHUNK_WORDS - _CHUNK_OVERLAP
    for start in range(0, len(words), step):
        piece = " ".join(words[start : start + _CHUNK_WORDS])
        if piece:
            yield piece
        if start + _CHUNK_WORDS >= len(words):
            break


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Stats histórico (sem embedding) — probabilidade de vitória por UF/sub_assunto.
# ---------------------------------------------------------------------------

def lookup_historical_win_rate(
    db, uf: str | None, sub_assunto: str | None, default: float = 0.30
) -> tuple[float, int]:
    """Retorna (probabilidade_vitoria, n_amostras) da SentencaHistorica.

    Puramente SQL (sem embedding). Útil para grounding do classifier e valuator.
    Resiliente: em qualquer falha devolve `(default, 0)`.
    """
    try:
        from app.db.models.sentenca_historica import SentencaHistorica

        q = db.query(SentencaHistorica)
        if uf:
            q = q.filter(SentencaHistorica.uf == uf)
        if sub_assunto:
            q = q.filter(SentencaHistorica.sub_assunto.ilike(sub_assunto))
        rows = q.limit(500).all()
        if not rows:
            return default, 0
        exitos = sum(
            1
            for r in rows
            if (r.resultado_macro or "").strip().lower().startswith("êxito")
        )
        prob = round(exitos / len(rows), 3)
        return prob, len(rows)
    except Exception as exc:  # noqa: BLE001
        logger.warning("lookup_historical_win_rate falhou: %s", exc)
        return default, 0
