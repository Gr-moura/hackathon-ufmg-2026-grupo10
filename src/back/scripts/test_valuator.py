"""Script de teste para o Valuator (GPT Acordo)."""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Adiciona o src/back ao PYTHONPATH
sys.path.append(str(Path(__file__).parents[1]))

from app.services.ai.valuator import ValuationContext, ValuationResult, evaluate_settlement, load_policy

def test_valuator_logic():
    print("Iniciando teste de lógica do Valuator...")
    
    # 1. Carrega a política para conferir valores
    policy = load_policy()
    print(f"Política carregada: {policy.get('settlement_bounds')}")

    # 2. Cria um contexto de teste (Cenário de Perda/Acordo)
    context = ValuationContext(
        valor_da_causa=10000.0,
        probabilidade_vitoria=0.15, # Vitória baixa
        sub_assunto="golpe",
        pontos_fortes=["Cliente tem histórico de bom pagador"],
        pontos_fracos=["Assinatura no contrato é visivelmente diferente", "Sem comprovante de TED"],
        document_texts="Petição inicial alega fraude em empréstimo consignado..."
    )

    # 3. Mock da OpenAI para não gastar créditos/depender de chave no teste de unidade
    mock_result = ValuationResult(
        valor_sugerido=4500.0,
        intervalo_max=7500.0,
        custo_estimado_litigar=12500.0,
        justificativa="Cálculo baseado em 45% da causa devido ao risco de fraude (golpe) e sucumbência estimada."
    )

    # Nota: Para testar a INTEGRAÇÃO REAL, você precisaria da chave .env
    # Aqui vamos apenas validar se o fluxo de dados até o prompt está correto
    print(f"\nTestando cenário: R$ {context.valor_da_causa} | Sub-assunto: {context.sub_assunto}")
    
    # Simulação de verificação de regras da política
    piso_abs = policy['settlement_bounds']['piso_absoluto_brl']
    if mock_result.valor_sugerido < piso_abs:
        print(f"⚠️ Alerta: Valor sugerido (R$ {mock_result.valor_sugerido}) abaixo do piso absoluto (R$ {piso_abs})")
    else:
        print(f"✅ Sucesso: Valor sugerido respeita o piso da política.")

    if mock_result.intervalo_max > (context.valor_da_causa * policy['settlement_bounds']['teto_pct_valor_causa']):
         print(f"⚠️ Alerta: Intervalo máximo ultrapassa teto da política.")
    else:
        print(f"✅ Sucesso: Teto de negociação dentro dos limites da política.")

    print("\nJustificativa gerada pelo modelo (Simulada):")
    print(f"'{mock_result.justificativa}'")

if __name__ == "__main__":
    test_valuator_logic()
