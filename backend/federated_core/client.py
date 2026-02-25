import torch
import torch.nn as nn
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, roc_auc_score

from models.mlp import SmallMLP


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

INPUT_FEATURES = [
    "age",
    "is_senior",
    "avg_heartrate",
    "min_o2_sat",
    "avg_bp",
    "max_WBC_x_1000",
    "max_creatinine",
    "max_glucose",
    "max_lactate",
    "max_potassium",
    "max_sodium",
]

INPUT_DIM = len(INPUT_FEATURES)
POS_WEIGHT = 19.1  # From earlier imbalance calculation


class FederatedClient:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.model = SmallMLP(INPUT_DIM).to(DEVICE)

    def load_data(self):
        df = pd.read_csv(self.csv_path)

        X = df[INPUT_FEATURES].values
        y = df["mortality"].values

        # ---- Local Imputation ----
        imputer = SimpleImputer(strategy="median")
        X = imputer.fit_transform(X)

        # ---- Local Standardization ----
        scaler = StandardScaler()
        X = scaler.fit_transform(X)

        X = torch.tensor(X, dtype=torch.float32).to(DEVICE)
        y = torch.tensor(y, dtype=torch.float32).unsqueeze(1).to(DEVICE)

        return X, y, df

    def train(self, global_weights=None, epochs=3, lr=0.001):

        if global_weights is not None:
            self.model.load_state_dict(global_weights)

        X, y, raw_df = self.load_data()

        pos_weight = torch.tensor([POS_WEIGHT]).to(DEVICE)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

        optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=lr,
            weight_decay=1e-4
        )

        self.model.train()

        for _ in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()

        metrics = self.evaluate(X, y, raw_df)

        return self.model.state_dict(), metrics

    def evaluate(self, X, y, raw_df):
        self.model.eval()

        with torch.no_grad():
            logits = self.model(X)
            probs = torch.sigmoid(logits).cpu().numpy()
            preds = (probs > 0.5).astype(int)

        y_true = y.cpu().numpy()

        accuracy = accuracy_score(y_true, preds)

        # ---- Safe AUC (avoid crash if single class) ----
        try:
            auc = roc_auc_score(y_true, probs)
        except ValueError:
            auc = 0.5  # fallback if only one class present

        # ---- Fairness: Demographic Parity Difference ----
        senior_mask = raw_df["is_senior"] == 1
        non_senior_mask = raw_df["is_senior"] == 0

        if senior_mask.sum() > 0 and non_senior_mask.sum() > 0:
            dp_senior = preds[senior_mask].mean()
            dp_non_senior = preds[non_senior_mask].mean()
            demographic_parity = abs(dp_senior - dp_non_senior)
        else:
            demographic_parity = 0.0

        return {
            "accuracy": float(accuracy),
            "auc": float(auc),
            "demographic_parity": float(demographic_parity),
            "samples": len(raw_df)
        }