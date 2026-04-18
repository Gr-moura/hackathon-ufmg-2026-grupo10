# Módulo de Inteligência Artificial (Final LLM)

Este diretório contém o componente principal de tomada de decisão do projeto, utilizando Modelos de Linguagem de Grande Escala (LLM) da OpenAI para analisar processos judiciais de forma autônoma.

## Componentes

### `main.py`
O script principal que integra a extração de documentos PDF com o raciocínio jurídico do GPT-4o-mini.

#### Funcionalidades:
- **Extração Inteligente**: Utiliza `pdfplumber` para converter documentos processuais (Peticao Inicial, Contratos, Extratos, etc.) em texto processável.
- **Raciocínio Jurídico**: Aplica um prompt de sistema especializado que simula um advogado sênior especialista em direito bancário.
- **Classificação Binária**: Decide entre:
  - `GANHA`: Quando há provas robustas de contratação (assinatura conferindo, comprovante de repasse de valores).
  - `DIFICIL`: Quando há vulnerabilidades (falta de documentos, assinaturas divergentes).
- **Valoração de Acordo Otimizada**:
  - Calcula valores entre 30% e 70% do valor da causa.
  - Utiliza o conhecimento interno da IA sobre jurisprudência brasileira para estimar o "gasto de uma defesa média" (danos morais + custas + honorários) e garante que a proposta de acordo seja financeiramente vantajosa para o banco.
- **Saída Estruturada**: Utiliza a funcionalidade de *Structured Outputs* da OpenAI para garantir que a resposta seja sempre um JSON válido seguindo o esquema `SettlementRecommendation`.

## Requisitos

- `openai>=1.54.0`
- `pdfplumber`
- `pydantic`
- `python-dotenv` (opcional, para carregar a chave da API)

## Como Usar

1. **Configurar a Chave**:
   Defina sua chave da OpenAI no ambiente:
   ```bash
   export OPENAI_API_KEY="sua_chave_aqui"
   ```

2. **Executar a Análise**:
   Aponte para uma pasta contendo os PDFs do processo:
   ```bash
   python models/final_llm/main.py "/caminho/para/pasta/do/processo" --valor 5000.0
   ```

## Prompt e Lógica de Decisão

O prompt foi desenhado para seguir a **Política de Acordos do Banco UFMG**, cruzando os fatos extraídos dos documentos com a probabilidade de êxito judicial. A IA é instruída a ser conservadora na defesa e agressiva no acordo quando a condenação for provável, sempre visando o lucro líquido (Economia = Custo Condenacao - Valor Acordo).
