import json
import os
import sys
import pandas as pd

# Adiciona o diretório atual ao path para importar RN1
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from RN1 import predict_litigation

def run_test_scenario(name, docs):
    base_case = {
        'UF': 'AM',
        'Assunto': 'Não reconhece operação',
        'Sub-assunto': 'Golpe',
        'Valor da causa': 10000.0,
        'Contrato': 0.0,
        'Extrato': 0.0,
        'Comprovante de crédito': 0.0,
        'Dossiê': 0.0,
        'Demonstrativo de evolução da dívida': 0.0,
        'Laudo referenciado': 0.0
    }
    # Update with document presence
    case = {**base_case, **docs}
    result_json = predict_litigation(case)
    result = json.loads(result_json)
    print(f"{name:.<40} | Win Prob: {result['probabilidade_vitoria']:.4f} | Loss Prob: {result['probabilidade_perda']:.4f}")
    return result['probabilidade_vitoria']

print("Testing Model Logic (RN1 Document Weights)")
print("-" * 80)

# Scenarios
scenarios = [
    ("1. No Documents", {}),
    
    # Core Proofs (Anuency)
    ("2. Only Contrato (Anuency)", {'Contrato': 1.0}),
    ("3. Only Dossie (Anuency)", {'Dossiê': 1.0}),
    
    # Core Proofs (Disbursement)
    ("4. Only Comprovante (Disbursement)", {'Comprovante de crédito': 1.0}),
    
    # Combined Core Proofs
    ("5. Contrato + Comprovante (Full Defense)", {'Contrato': 1.0, 'Comprovante de crédito': 1.0}),
    ("6. Dossie + Comprovante (Full Defense)", {'Dossiê': 1.0, 'Comprovante de crédito': 1.0}),
    
    # Supporting Proofs (Acessórios)
    ("7. Only Extrato", {'Extrato': 1.0}),
    ("8. Only Demonstrativo", {'Demonstrativo de evolução da dívida': 1.0}),
    ("9. Only Laudo Referenciado", {'Laudo referenciado': 1.0}),
    ("10. All Supporting (No Core)", {'Extrato': 1.0, 'Demonstrativo de evolução da dívida': 1.0, 'Laudo referenciado': 1.0}),
    
    # Supporting + One Core
    ("11. Contrato + All Supporting", {'Contrato': 1.0, 'Extrato': 1.0, 'Demonstrativo de evolução da dívida': 1.0, 'Laudo referenciado': 1.0}),
    ("12. Comprovante + All Supporting", {'Comprovante de crédito': 1.0, 'Extrato': 1.0, 'Demonstrativo de evolução da dívida': 1.0, 'Laudo referenciado': 1.0}),
]

results = []
for name, docs in scenarios:
    results.append(run_test_scenario(name, docs))

print("-" * 80)
# Analysis
print("\nLogic Analysis:")
if results[4] > results[9]:
    print("[PASS] Full Defense (Contrato + Comprovante) has higher win prob than All Supporting Docs.")
else:
    print("[FAIL] Supporting docs have too much weight compared to Core Proofs.")

if results[4] > results[1]:
    print("[PASS] Adding Comprovante to Contrato increases win prob.")
else:
    print("[FAIL] Comprovante did not increase win prob when added to Contrato.")

if results[9] < results[1] or results[9] < results[3] or results[9] < results[4]:
    print("[PASS] Supporting docs alone have relatively low impact compared to Core Proofs.")
else:
    print("[FLAG] Supporting docs alone might have high impact.")
