import torch
import torch.nn as nn
import torch.nn.functional as F

class LitigationModel(nn.Module):
    """
    Neural Network for deciding between Defense or Agreement.
    Multi-task architecture:
    1. Classification: Predicts the outcome (Win, Partial Loss, Total Loss)
    2. Regression: Predicts the expected condemnation value
    """
    def __init__(self, input_dim, hidden_dims=[128, 64, 32], dropout_rate=0.2):
        super(LitigationModel, self).__init__()
        
        # Shared Layers (Feature Extraction)
        layers = []
        last_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(last_dim, h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.Dropout(dropout_rate))
            last_dim = h_dim
        
        self.shared_backbone = nn.Sequential(*layers)
        
        # Head 1: Outcome Classification (0: VITORIA/IMPROCEDENTE, 1: PERDA/PARCIAL OU PROCEDENTE)
        self.classifier_head = nn.Sequential(
            nn.Linear(last_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 2) # 2 classes: Win or Loss
        )
        
        # Head 2: Value Regression (Expected Condemnation Value)
        self.regressor_head = nn.Sequential(
            nn.Linear(last_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1) # Single scalar value
        )

    def forward(self, x):
        features = self.shared_backbone(x)
        
        logits = self.classifier_head(features)
        value = self.regressor_head(features)
        
        return logits, value

def calculate_loss(logits, pred_value, target_class, target_value, alpha=0.5):
    """
    Combined loss for multi-task learning.
    alpha: Weight for classification loss vs regression loss.
    """
    # Classification Loss (CrossEntropy)
    class_loss = F.cross_entropy(logits, target_class)
    
    # Regression Loss (MSE or Hubber)
    reg_loss = F.mse_loss(pred_value.squeeze(), target_value)
    
    return alpha * class_loss + (1 - alpha) * reg_loss
