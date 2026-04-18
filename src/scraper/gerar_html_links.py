"""Gera uma página HTML com todos os links de processos para abrir com extensão de browser."""
import json
import sys
from pathlib import Path


def formatar_numero(n: str) -> str:
    n = n.replace("-", "").replace(".", "")
    if len(n) != 20:
        return n
    return f"{n[:7]}-{n[7:9]}.{n[9:13]}.{n[13]}.{n[14:16]}.{n[16:]}"


CONSULTA_URLS = {
    "tjam": "https://pje.tjam.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjal": "https://pje2.tjal.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjce": "https://pje.tjce.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjma": "https://pje.tjma.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjpb": "https://pje.tjpb.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjpe": "https://pje.tjpe.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjpi": "https://pje.tjpi.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjrn": "https://pje.tjrn.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjse": "https://pje.tjse.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjto": "https://pje.tjto.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjac": "https://pje.tjac.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjap": "https://pje.tjap.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjro": "https://pje.tjro.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjrr": "https://pje.tjrr.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjpa": "https://pje.tjpa.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjgo": "https://pje.tjgo.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjmt": "https://pje.tjmt.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjms": "https://pje.tjms.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjdft": "https://pje.tjdft.jus.br/pje/ConsultaPublica/listView.seam?numeroProcesso={}",
    "tjsp": "https://esaj.tjsp.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&dadosConsulta.valorConsulta={}",
    "tjba": "https://esaj.tjba.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&dadosConsulta.valorConsulta={}",
    "tjsc": "https://esaj.tjsc.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&dadosConsulta.valorConsulta={}",
    "tjrs": "https://eproc.tjrs.jus.br/eproc/externo_controlador.php?acao=processo_consulta_publica&num_processo={}",
    "tjes": "https://eproc.tjes.jus.br/eproc/externo_controlador.php?acao=processo_consulta_publica&num_processo={}",
    "tjmg": "https://www4.tjmg.jus.br/juridico/sf/proc_resultado2.jsp?listaProcessos={}",
    "tjrj": "https://www4.tjrj.jus.br/consultaProcessoWebV2/consultaMov.do?v=2&numProcesso={}",
    "tjpr": "https://projudi.tjpr.jus.br/projudi/",
}


def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else "data/processos.json"
    saida = sys.argv[2] if len(sys.argv) > 2 else "data/links_processos.html"

    processos = json.loads(Path(json_path).read_text())
    linhas_html = []

    for p in processos:
        numero_raw = p.get("numeroProcesso", "")
        tribunal = p.get("_tribunal", "")
        numero_fmt = formatar_numero(numero_raw)
        template = CONSULTA_URLS.get(tribunal, "")
        if not template:
            continue
        url = template.format(numero_fmt)
        classe = p.get("classe", {}).get("nome", "")
        linhas_html.append(f'<li><a href="{url}" target="_blank">[{tribunal.upper()}] {numero_fmt} — {classe}</a></li>')

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Links de Processos — {len(linhas_html)} processos</title>
<style>
  body {{ font-family: monospace; padding: 20px; }}
  h1 {{ font-size: 1.2rem; }}
  li {{ margin: 4px 0; }}
  a {{ color: #0057b7; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  #abrir-tudo {{ margin: 16px 0; padding: 8px 16px; background: #0057b7; color: white; border: none; cursor: pointer; font-size: 1rem; border-radius: 4px; }}
</style>
</head>
<body>
<h1>Links de Consulta Pública — {len(linhas_html)} processos</h1>
<p>Instale o <b>Tampermonkey</b> + o script <code>tampermonkey_pje.js</code> e clique em "Abrir Todos".<br>
O script baixará os PDFs automaticamente em cada aba.</p>
<button id="abrir-tudo">Abrir Todos (abre {len(linhas_html)} abas)</button>
<ul id="lista">
{"".join(linhas_html)}
</ul>
<script>
document.getElementById('abrir-tudo').addEventListener('click', function() {{
  const links = document.querySelectorAll('#lista a');
  links.forEach(function(a, i) {{
    setTimeout(function() {{ window.open(a.href, '_blank'); }}, i * 800);
  }});
}});
</script>
</body>
</html>"""

    Path(saida).write_text(html, encoding="utf-8")
    print(f"{len(linhas_html)} links → {saida}")


if __name__ == "__main__":
    main()
