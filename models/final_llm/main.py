import os
import sys
import argparse
import json
from pathlib import Path
from typing import List

import pdfplumber
import openai
from pydantic import BaseModel, Field

# ==========================================
# 1. DEFINIÇÃO DO SCHEMA PARA O LLM (Cego para estatísticas)
# ==========================================
class AvaliacaoProvas(BaseModel):
    raciocinio_juridico: str = Field(
        description="Análise técnica e estrita das provas materiais justificando a nota escolhida."
    )
    nota_das_provas: float = Field(
        description="Nota de 0.0 a 100.0 avaliando apenas a força documental da defesa."
    )
    positive_points: List[str] = Field(
        description="Lista detalhada das provas materiais fortes encontradas."
    )
    negative_points: List[str] = Field(
        description="Lista detalhada dos riscos, falta de documentos e vulnerabilidades."
    )

# ==========================================
# 2. FUNÇÕES AUXILIARES
# ==========================================
def load_openai_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key

def extract_text_from_pdfs(directory_path: str) -> str:
    path = Path(directory_path)
    combined_text = ""
    
    if not path.is_dir():
        raise NotADirectoryError(f"O caminho '{directory_path}' não é um diretório válido.")

    for pdf_file in path.glob("*.pdf"):
        try:
            with pdfplumber.open(pdf_file) as pdf:
                combined_text += f"\n--- DOCUMENTO: {pdf_file.name} ---\n"
                for page in pdf.pages:
                    combined_text += (page.extract_text() or "") + "\n"
        except Exception as e:
            print(f"Aviso: Erro ao ler o PDF {pdf_file.name}: {e}")
            
    return combined_text

# ==========================================
# 3. INTEGRAÇÃO COM OPENAI & LÓGICA MATEMÁTICA
# ==========================================
def analisar_processo(textos_documentos: str, probabilidade_derrota: float, client: openai.OpenAI) -> dict:
    
    # 1. O LLM AVALIA APENAS OS DOCUMENTOS (Análise Qualitativa)
    system_prompt = """
    Você é um advogado sênior especialista em direito bancário.
    Sua tarefa é ler os documentos do processo e fazer uma ANÁLISE QUALITATIVA da força da defesa do banco, gerando uma nota de 0.0 a 100.0.

    ### DIRETRIZES DE AVALIAÇÃO QUALITATIVA:
    1. ANALISE O CONJUNTO PROBATÓRIO: Não avalie apenas a presença do documento, mas a *qualidade* da prova. A assinatura no contrato bate com o laudo? O comprovante de TED mostra que o dinheiro realmente caiu na conta e foi usado? A defesa é coesa?
    2. DEFINIÇÃO DA NOTA: Baseie sua nota na solidez do caso do banco.
       - Notas altas (ex: 80 a 100): Defesa irrefutável, provas documentais coesas e consistentes (Contrato + Laudo favorável + TED indiscutível).
       - Notas médias (ex: 40 a 79): Provas documentais presentes, mas com fragilidades, contradições ou vulnerabilidades inerentes (como hipervulnerabilidade do consumidor).
       - Notas baixas (ex: 0 a 39): Defesa frágil, ausência de assinatura validada, ou indícios de fraude.

    ### REGRAS DO JSON:
    - 'raciocinio_juridico': Discorra qualitativamente sobre a força das provas e o mérito da defesa do banco de forma natural, como um parecer jurídico.
    - 'nota_das_provas': O valor numérico de 0.0 a 100.0 que resume sua análise técnica.
    - 'positive_points': Liste os pontos fortes qualitativos da defesa.
    - 'negative_points': Liste os riscos jurídicos e fragilidades.
    """

    user_prompt = f"""
    ### TEXTO EXTRAÍDO DOS DOCUMENTOS DOS AUTOS ###
    {textos_documentos}

    Analise as provas e retorne o JSON estruturado.
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=AvaliacaoProvas,
        temperature=0.0  # Mantém a previsibilidade da análise para o mesmo texto
    )
    
    avaliacao = response.choices[0].message.parsed

    # ==========================================
    # 2. A MATEMÁTICA É FEITA NO PYTHON E MANTIDA INVISÍVEL
    # ==========================================
    # Ajuste leve da estatística
    ajuste_estatistico = (50.0 - probabilidade_derrota) / 3.0
    
    # Aplica o ajuste na nota do especialista
    confidence_score = avaliacao.nota_das_provas + ajuste_estatistico
    
    # Trava matemática para manter entre 0 e 100
    confidence_score = max(0.0, min(100.0, confidence_score))
    
    # Define tendência e orientação
    trend = "VITÓRIA" if confidence_score > 50.0 else "DERROTA"
    
    if confidence_score <= 20.0:
        orientacao = "Chance de derrota muito alta. Defesa altamente não recomendada (sugere-se acordo)."
    elif confidence_score <= 50.0:
        orientacao = "Chance maior de derrota. Risco elevado."
    elif confidence_score <= 70.0:
        orientacao = "Chance boa de vitória. Defesa viável."
    else:
        orientacao = "Ótimas chances de vitória. Seguir com defesa robusta."

    # 3. MONTA O JSON FINAL (Ocultando a matemática)
    resultado_final = {
        "raciocinio_juridico": avaliacao.raciocinio_juridico,
        "confidence_score": round(confidence_score, 2),
        "orientacao_advogado": orientacao,
        "trend": trend,
        "positive_points": avaliacao.positive_points,
        "negative_points": avaliacao.negative_points
    }
    
    return resultado_final

# ==========================================
# 4. EXECUÇÃO PRINCIPAL
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Análise Jurídica de Defesa com LLM")
    parser.add_argument("path", type=str, help="Caminho para o diretório com os PDFs")
    parser.add_argument("--chance_derrota", type=float, required=True, help="Probabilidade de derrota calculada pelo modelo (0 a 100)")
    args = parser.parse_args()

    api_key = load_openai_key()
    if not api_key:
        print("Erro: API Key não encontrada.")
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)

    print("Extraindo texto dos documentos localmente...")
    textos_extraidos = extract_text_from_pdfs(args.path)
    
    if not textos_extraidos.strip():
        print("Erro: Nenhum texto foi extraído.")
        sys.exit(1)

    print(f"Analisando caso (Chance de Derrota pré-calculada: {args.chance_derrota}%)...")
    try:
        resultado_dict = analisar_processo(textos_extraidos, args.chance_derrota, client)
        
        print("\n=== SAÍDA JSON ===")
        print(json.dumps(resultado_dict, indent=4, ensure_ascii=False))
        
    except Exception as e:
        print(f"Erro ao processar a requisição: {e}")

if __name__ == "__main__":
    main()