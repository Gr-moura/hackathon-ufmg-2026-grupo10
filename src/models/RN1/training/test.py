import torch
import numpy as np
import pandas as pd
import os
from model import LitigationModel
from dataset import LitigationDataset

def run_inference():
    # 1. Load Data to initialize encoders and scaler
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resultados_path = os.path.join(current_dir, "resultados_dos_processos.csv")
    subsidios_path = os.path.join(current_dir, "subsidios_disponibilizados.csv")
    
    print(f"Initializing encoders/scaler from {resultados_path} and {subsidios_path}...")
    if not os.path.exists(resultados_path) or not os.path.exists(subsidios_path):
        raise FileNotFoundError("Required CSV files for test initialization not found.")
        
    df_res = pd.read_csv(resultados_path)
    df_sub = pd.read_csv(subsidios_path)
    
    # Merge on process number. Note the typo 'processos' in subsidios file
    merge_col_res = 'Número do processo'
    merge_col_sub = 'Número do processos' if 'Número do processos' in df_sub.columns else 'Número do processo'
    
    df_merged = pd.merge(df_res, df_sub, left_on=merge_col_res, right_on=merge_col_sub, how='left')
    
    dataset = LitigationDataset(dataframe=df_merged)
    
    # 2. Load Model
    input_dim = len(dataset.feature_cols)
    model = LitigationModel(input_dim=input_dim)
    
    # Load weights
    root_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
    model_path = os.path.join(root_dir, "models", "litigation_model.pth")
    try:
        model.load_state_dict(torch.load(model_path))
        print(f"Loaded saved model weights from {model_path}")
    except:
        print(f"Could not load weights from {model_path}. Using uninitialized weights.")
    
    model.eval()
    
    # 3. Simulate a new case
    # Now includes document presence flags (1.0 for present, 0.0 for absent)
    new_case = {
        'UF': 'SP',
        'Assunto': 'Não reconhece operação',
        'Sub-assunto': 'Golpe',
        'Valor da causa': 15000.0,
        'Contrato': 0.0,
        'Extrato': 0.0,
        'Comprovante de crédito': 0.0,
        'Dossiê': 1.0,
        'Demonstrativo de evolução da dívida': 0.0,
        'Laudo referenciado': 1.0
    }
    
    # Preprocess
    # Use label encoders for categorical fields
    x_raw = []
    for col in dataset.feature_cols:
        val = new_case.get(col, 0.0) # Default to 0 if column missing in simulation
        if col in dataset.label_encoders:
            # Handle unknown labels by defaulting to the first class
            try:
                val = dataset.label_encoders[col].transform([str(val)])[0]
            except ValueError:
                print(f"Warning: Unknown label '{val}' for column '{col}'. Using default.")
                val = 0
        x_raw.append(val)
    
    x_input = np.array([x_raw], dtype=np.float32)
    x_input = dataset.scaler.transform(x_input)
    x_tensor = torch.from_numpy(x_input)
    
    # Predict
    with torch.no_grad():
        logits, pred_val = model(x_tensor)
        probs = torch.nn.functional.softmax(logits, dim=1)
        
    # Results
    outcomes = ['VITORIA (Win)', 'PERDA (Loss)']
    pred_class = torch.argmax(probs).item()
    
    p_win = probs[0, 0].item()
    expected_loss = (1 - p_win) * pred_val.item()
    
    print("\n--- Litigation Analysis Report ---")
    print(f"Case Data: {new_case}")
    print(f"Probabilities: {dict(zip(outcomes, probs[0].tolist()))}")
    print(f"Predicted Outcome: {outcomes[pred_class]}")
    print(f"Estimated Condemnation Value: R$ {pred_val.item():.2f}")
    print(f"Expected Loss (Weighted): R$ {expected_loss:.2f}")

if __name__ == "__main__":
    run_inference()
