import time
import os
from fl_core.client import HospitalClient

# SHARED STATE for the Dashboard
DASHBOARD_STATE = {
    "round": 0,
    "accuracy": 0.60,
    "logs": [],
    "clients": {"Hospital A": 0, "Hospital B": 0}
}

def run_simulation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize Clients
    client_a = HospitalClient("Hospital A", os.path.join(base_dir, 'data', 'hospital_A_fair.csv'))
    client_b = HospitalClient("Hospital B", os.path.join(base_dir, 'data', 'hospital_B_biased.csv'))
    
    DASHBOARD_STATE["logs"].append("System Initialized. Waiting for start...")
    time.sleep(2)
    
    # Run 5 Rounds
    for r in range(1, 6):
        DASHBOARD_STATE["round"] = r
        DASHBOARD_STATE["logs"].append(f"--- Starting Round {r} ---")
        time.sleep(2)
        
        # Client A Train
        res_a = client_a.train_and_validate()
        DASHBOARD_STATE["clients"]["Hospital A"] = res_a["bias_score"]
        DASHBOARD_STATE["logs"].append(f"Hospital A Update Rx: Bias Score {res_a['bias_score']} (Safe)")
        time.sleep(2)
        
        # Client B Train
        res_b = client_b.train_and_validate()
        DASHBOARD_STATE["clients"]["Hospital B"] = res_b["bias_score"]
        
        if res_b["bias_score"] > 0.15:
            DASHBOARD_STATE["logs"].append(f"ALERT: Hospital B Bias Score {res_b['bias_score']} exceeds threshold!")
            DASHBOARD_STATE["logs"].append(f"Action: Rejecting Hospital B update.")
        else:
            DASHBOARD_STATE["logs"].append(f"Hospital B Update Rx: Bias Score {res_b['bias_score']}")
            
        # Mock Global Aggregation Improvement
        DASHBOARD_STATE["accuracy"] += 0.02
        time.sleep(2)

if __name__ == "__main__":
    run_simulation()