from sklearn.linear_model import LogisticRegression
from bias_engine.detector import BiasDetector
import pandas as pd
import numpy as np

class HospitalClient:
    def __init__(self, hospital_name, data_path):
        self.name = hospital_name
        self.data = pd.read_csv(data_path)
        self.model = LogisticRegression()
        self.detector = BiasDetector()
        
    def train_and_validate(self):
        # Prepare Data
        X = self.data[['age', 'is_senior']].values
        y = self.data['mortality'].values
        
        # Train Local Model
        self.model.fit(X, y)
        
        # Predict on self to check internal bias
        preds = self.model.predict(X)
        
        # Calculate Bias
        bias_score = self.detector.check_demographic_parity(X, preds)
        
        return {
            "client": self.name,
            "bias_score": round(bias_score, 4),
            "weights": self.model.coef_.tolist()
        }