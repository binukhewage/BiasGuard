import numpy as np

class BiasDetector:
    def check_demographic_parity(self, X, y_pred, sensitive_idx=1):
        """
        Calculates difference in positive predictions between Groups.
        Sensitive Feature is at index 1 ('is_senior').
        """
        # Split predictions by group
        seniors = [y_pred[i] for i in range(len(X)) if X[i][sensitive_idx] == 1]
        young = [y_pred[i] for i in range(len(X)) if X[i][sensitive_idx] == 0]
        
        # Calculate Rate of Mortality Prediction
        rate_seniors = np.mean(seniors) if seniors else 0
        rate_young = np.mean(young) if young else 0
        
        # The Score: How different are they?
        bias_score = abs(rate_seniors - rate_young)
        return bias_score