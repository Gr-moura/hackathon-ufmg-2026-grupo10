import torch
import numpy as np
import pandas as pd
import os
import sys
import json

# Adiciona o diretório de treinamento ao path para importar as definições do modelo e dataset
training_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training")
if training_dir not in sys.path:
    sys.path.append(training_dir)

try:
    from model import LitigationModel
    from dataset import LitigationDataset
except ImportError:
    # Caso seja chamado de fora com caminhos diferentes
    from .training.model import LitigationModel
    from .training.dataset import LitigationDataset

class LitigationPredictor:
    """
    Classe utilitária para gerenciar o carregamento do modelo e inferência.
    Carrega o dataset de treino para reconstruir os Encoders e Scaler (padrão atual do projeto).
    """
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        training_dir = os.path.join(current_dir, "training")
        
        # Caminhos dos dados para inicializar o preprocessamento
        resultados_path = os.path.join(training_dir, "resultados_dos_processos.csv")
        subsidios_path = os.path.join(training_dir, "subsidios_disponibilizados.csv")
        
        if not os.path.exists(resultados_path):
            raise FileNotFoundError(f"Arquivo de resultados não encontrado em {resultados_path}")

        # Merge dos datasets para obter o estado completo dos Encoders
        df_res = pd.read_csv(resultados_path)
        df_merged = df_res
        if os.path.exists(subsidios_path):
            df_sub = pd.read_csv(subsidios_path)
            merge_col_sub = 'Número do processos' if 'Número do processos' in df_sub.columns else 'Número do processo'
            df_merged = pd.merge(df_res, df_sub, left_on='Número do processo', right_on=merge_col_sub, how='left')
        
        # Inicializa o dataset (isso reconstrói LabelEncoders e o StandardScaler)
        self.dataset = LitigationDataset(dataframe=df_merged)
        
        # Inicializa o modelo
        input_dim = len(self.dataset.feature_cols)
        self.model = LitigationModel(input_dim=input_dim)
        
        # Carrega os pesos do modelo
        # hackathon-ufmg-2026/src/models/RN1/RN1.py -> root/models/litigation_model.pth
        root_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        model_path = os.path.join(root_dir, "models", "litigation_model.pth")
        
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        
        self.model.eval()

    def predict(self, case_data):
        """
        Executa a predição para um dicionário de entrada.
        """
        # Prepara o vetor de características
        x_raw = []
        for col in self.dataset.feature_cols:
            val = case_data.get(col, 0.0)
            if col in self.dataset.label_encoders:
                try:
                    val = self.dataset.label_encoders[col].transform([str(val)])[0]
                except (ValueError, KeyError):
                    val = 0 # Default para categoria desconhecida
            x_raw.append(val)
        
        # Normalização e conversão para Tensor
        x_input = np.array([x_raw], dtype=np.float32)
        x_input = self.dataset.scaler.transform(x_input)
        x_tensor = torch.from_numpy(x_input)
        
        # Inferência
        with torch.no_grad():
            logits, pred_val = self.model(x_tensor)
            probs = torch.nn.functional.softmax(logits, dim=1).numpy()[0]
            
        prob_vitoria = float(probs[0])
        prob_perda = float(probs[1])
        valor_condenacao = float(pred_val.item())
        
        # Resultado legível
        return {
            'probabilidade_vitoria': round(prob_vitoria, 4),
            'probabilidade_perda': round(prob_perda, 4),
            'resultado_predominante': 'VITORIA' if prob_vitoria > prob_perda else 'PERDA',
            'valor_estimado_condenacao': round(valor_condenacao, 2),
            'perda_esperada_ponderada': round(prob_perda * valor_condenacao, 2)
        }

# Singleton para evitar recarregar o dataset/modelo em cada chamada
_predictor = None

def predict_litigation(case_data):
    """
    Função principal chamável para rodar o modelo RN1.
    Recebe um dicionário com os dados do processo e retorna as probabilidades e valores.
    """
    global _predictor
    if _predictor is None:
        _predictor = LitigationPredictor()
    return json.dumps(_predictor.predict(case_data))

if __name__ == "__main__":
    # Exemplo de uso
    test_case = {
        'UF': 'AM',
        'Assunto': 'Não reconhece operação',
        'Sub-assunto': 'Golpe',
        'Valor da causa': 15000.0,
        'Contrato': 1.0,
        'Extrato': 1.0,
        'Comprovante de crédito': 0.0,
        'Dossiê': 1.0,
        'Demonstrativo de evolução da dívida': 1.0,
        'Laudo referenciado': 0.0
    }
    print(predict_litigation(test_case))
