"""Gera links de consulta pública formatados para cada processo do JSON do DataJud."""
from __future__ import annotations

import json
import csv
import sys
from pathlib import Path

CONSULTA_URLS: dict[str, str] = {
    "tjam":  "https://pje.tjam.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjal":  "https://pje2.tjal.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjce":  "https://pje.tjce.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjma":  "https://pje.tjma.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjpb":  "https://pje.tjpb.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjpe":  "https://pje.tjpe.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjpi":  "https://pje.tjpi.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjrn":  "https://pje.tjrn.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjse":  "https://pje.tjse.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjto":  "https://pje.tjto.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjac":  "https://pje.tjac.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjap":  "https://pje.tjap.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjro":  "https://pje.tjro.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjrr":  "https://pje.tjrr.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjpa":  "https://pje.tjpa.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjgo":  "https://pje.tjgo.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjmt":  "https://pje.tjmt.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjms":  "https://pje.tjms.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjdft": "https://pje.tjdft.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjsp":  "https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&numeroDigitoAnoUnificado={}&foroNumeroUnificado=&dadosConsulta.valorConsultaNuUnificado={}&dadosConsulta.valorConsulta=&dadosConsulta.tipoNuProcesso=UNIFICADO",
    "tjba":  "https://esaj.tjba.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&dadosConsulta.valorConsulta={}",
    "tjsc":  "https://esaj.tjsc.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&dadosConsulta.valorConsulta={}",
    "tjmg":  "https://www4.tjmg.jus.br/juridico/sf/proc_resultado2.jsp?listaProcessos={}",
    "tjpr":  "https://projudi.tjpr.jus.br/projudi/",
    "tjrj":  "https://www4.tjrj.jus.br/consultaProcessoWebV2/consultaMov.do?v=2&codigo={}",
    "tjrs":  "https://www.tjrs.jus.br/site/busca-solr/index.html?q={}",
    "tjes":  "https://eproc.tjes.jus.br/eproc/externo_controlador.php?acao=processo_consulta_publica&num_processo={}",
    "tjrn":  "https://pje.tjrn.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
}


def formatar_numero(numero_raw: str) -> str:
    """Converte NNNNNNNDDAAAAJTTOOOO → NNNNNNN-DD.AAAA.J.TT.OOOO"""
    n = numero_raw.replace("-", "").replace(".", "")
    if len(n) != 20:
        return numero_raw
    return f"{n[:7]}-{n[7:9]}.{n[9:13]}.{n[13]}.{n[14:16]}.{n[16:]}"


def gerar_links(json_path: str, saida_csv: str) -> None:
    processos = json.loads(Path(json_path).read_text())
    linhas = []

    for p in processos:
        numero_raw = p.get("numeroProcesso", "")
        tribunal = p.get("_tribunal", "")
        numero_fmt = formatar_numero(numero_raw)
        raw_assuntos = p.get("assuntos", [])
        flat = []
        for a in raw_assuntos:
            if isinstance(a, dict):
                flat.append(a)
            elif isinstance(a, list):
                flat.extend(x for x in a if isinstance(x, dict))
        assuntos = ", ".join(a.get("nome", "") for a in flat if a.get("nome"))
        classe = p.get("classe", {}).get("nome", "")

        template = CONSULTA_URLS.get(tribunal, "")
        if "tjsp" in tribunal:
            # TJSP usa partes separadas do número
            partes = numero_fmt.split("-")[0] + "-" + numero_fmt.split("-")[1].split(".")[0]
            foro = numero_fmt.split(".")[-1]
            url = template.format(partes, numero_fmt, numero_fmt)
        else:
            url = template.format(numero_fmt) if template else ""

        linhas.append({
            "tribunal": tribunal.upper(),
            "numero_formatado": numero_fmt,
            "numero_raw": numero_raw,
            "classe": classe,
            "assuntos": assuntos,
            "url_consulta": url,
        })

    with open(saida_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=linhas[0].keys())
        writer.writeheader()
        writer.writerows(linhas)

    print(f"{len(linhas)} links gerados → {saida_csv}")


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "data/processos.json"
    saida = sys.argv[2] if len(sys.argv) > 2 else "data/links_processos.csv"
    gerar_links(json_path, saida)
