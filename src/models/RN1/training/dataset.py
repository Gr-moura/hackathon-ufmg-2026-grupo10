import pandas as pd
import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import StandardScaler, LabelEncoder
import numpy as np
import os

class LitigationDataset(Dataset):
    def __init__(self, csv_path=None, dataframe=None):
        if csv_path:
            self.df = pd.read_csv(csv_path)
        elif dataframe is not None:
            self.df = dataframe
        else:
            raise ValueError("Either csv_path or dataframe must be provided")

        self.base_features = ['UF', 'Sub-assunto', 'Valor da causa']
        self.doc_features = [
            'Contrato', 'Extrato', 'Comprovante de crédito', 'Dossiê',
            'Demonstrativo de evolução da dívida', 'Laudo referenciado'
        ]
        
        # Determine available features
        self.feature_cols = [col for col in self.base_features if col in self.df.columns]
        self.feature_cols += [col for col in self.doc_features if col in self.df.columns]
        
        self.target_class_col = 'Resultado micro'
        self.target_value_col = 'Valor da condenação/indenização'

        self._preprocess()

    def _preprocess(self):
        # Convert numeric strings with Brazilian format (1.234,56) to float
        for col in ['Valor da causa', 'Valor da condenação/indenização']:
            if col in self.df.columns and self.df[col].dtype == object:
                self.df[col] = self.df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
        
        if self.target_value_col in self.df.columns:
            self.df[self.target_value_col] = self.df[self.target_value_col].fillna(0.0)
        
        if 'Valor da causa' in self.df.columns:
            self.df['Valor da causa'] = self.df['Valor da causa'].fillna(self.df['Valor da causa'].median())

        # Label encode categories
        self.label_encoders = {}
        for col in ['UF', 'Sub-assunto']:
            if col in self.df.columns:
                le = LabelEncoder()
                self.df[col] = le.fit_transform(self.df[col].astype(str))
                self.label_encoders[col] = le

        # Fill missing document flags with 0 (assume absent if not in data)
        for col in self.doc_features:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna(0).astype(np.float32)

        # Map classes (Binary: Win vs Loss)
        # 0: VITORIA (Improcedência/Extinção)
        # 1: PERDA (Parcial procedência/Acordo/Procedência)
        class_map = {
            'Improcedência': 0,
            'Extinção': 0,
            'Parcial procedência': 1,
            'Acordo': 1,
            'Procedência': 1
        }
        if self.target_class_col in self.df.columns:
            self.df['target_class'] = self.df[self.target_class_col].map(class_map).fillna(0).astype(int)
            self.y_class = self.df['target_class'].values.astype(np.int64)
        else:
            self.y_class = np.zeros(len(self.df), dtype=np.int64)

        if self.target_value_col in self.df.columns:
            self.y_val = self.df[self.target_value_col].values.astype(np.float32)
        else:
            self.y_val = np.zeros(len(self.df), dtype=np.float32)

        # Features matrix
        self.X = self.df[self.feature_cols].values.astype(np.float32)

        # Scaling
        self.scaler = StandardScaler()
        self.X = self.scaler.fit_transform(self.X)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx]), torch.tensor(self.y_class[idx]), torch.tensor(self.y_val[idx])