"""Cliente da API pública do DataJud (CNJ).

Busca números de processo de todos os TJs filtrados por assunto
de não reconhecimento de operação de empréstimo/fraude bancária.
"""
from __future__ import annotations

import time
import requests

API_KEY = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
BASE_URL = "https://api-publica.datajud.cnj.jus.br"

TRIBUNAIS = [
    "tjac", "tjal", "tjam", "tjap", "tjba", "tjce", "tjdft",
    "tjes", "tjgo", "tjma", "tjmg", "tjms", "tjmt", "tjpa",
    "tjpb", "tjpe", "tjpi", "tjpr", "tjrj", "tjrn", "tjro",
    "tjrr", "tjrs", "tjsc", "tjse", "tjsp", "tjto",
]

# Assuntos CNJ relevantes para casos de não reconhecimento de operação bancária/fraude
ASSUNTOS = [
    "Contratos Bancários",
    "Empréstimo consignado",
    "Outras fraudes",
    "Cédula de Crédito Bancário",
    "Cartão de Crédito",
]

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}


def _build_query(assunto: str, page_size: int = 100, search_after: list | None = None) -> dict:
    query: dict = {
        "size": page_size,
        "sort": [{"dataAjuizamento": "desc"}, {"numeroProcesso.keyword": "asc"}],
        "_source": ["numeroProcesso", "tribunal", "assuntos", "classe", "dataAjuizamento", "orgaoJulgador"],
        "query": {
            "term": {"assuntos.nome.keyword": assunto}
        },
    }
    if search_after:
        query["search_after"] = search_after
    return query


def buscar_processos(
    tribunal: str,
    max_resultados: int = 200,
    delay: float = 1.0,
) -> list[dict]:
    """Busca processos de um tribunal específico e retorna lista de metadados."""
    url = f"{BASE_URL}/api_publica_{tribunal}/_search"
    resultados: list[dict] = []
    search_after = None

    for assunto in ASSUNTOS:
        if len(resultados) >= max_resultados:
            break

        page_size = min(100, max_resultados - len(resultados))
        query = _build_query(assunto, page_size=page_size, search_after=search_after)

        try:
            resp = requests.post(url, headers=HEADERS, json=query, timeout=30)
            resp.raise_for_status()
            hits = resp.json().get("hits", {}).get("hits", [])
            for hit in hits:
                src = hit["_source"]
                src["_tribunal"] = tribunal
                src["_sort"] = hit.get("sort")
                resultados.append(src)
            time.sleep(delay)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                pass  # tribunal sem índice
            else:
                print(f"  [{tribunal}] HTTP {e.response.status_code}: {e}")
        except Exception as e:
            print(f"  [{tribunal}] Erro: {e}")

    return resultados


def buscar_todos_tribunais(
    max_por_tribunal: int = 40,
    delay: float = 1.0,
) -> list[dict]:
    """Busca processos em todos os TJs e retorna lista consolidada."""
    todos: list[dict] = []
    for tribunal in TRIBUNAIS:
        print(f"Consultando {tribunal.upper()}…")
        processos = buscar_processos(tribunal, max_resultados=max_por_tribunal, delay=delay)
        print(f"  {len(processos)} processo(s) encontrado(s)")
        todos.extend(processos)
    return todos
