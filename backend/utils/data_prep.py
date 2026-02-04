import pandas as pd
import numpy as np
import os

def prepare_demo_data():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    raw_path = os.path.join(base_dir, 'data', 'patient.csv')
    
    print(f"Loading {raw_path}...")
    df = pd.read_csv(raw_path)

    # 1. Clean Data
    # Map Target: Alive=0, Expired=1
    df = df.dropna(subset=['hospitaldischargestatus', 'age'])
    df['mortality'] = df['hospitaldischargestatus'].map({'Alive': 0, 'Expired': 1})
    
    # Map Features: Age > 89 becomes 90
    df['age'] = df['age'].replace('> 89', '90').astype(int)
    df['is_senior'] = (df['age'] > 65).astype(int)
    
    # Keep only what we need for the demo
    demo_df = df[['age', 'is_senior', 'mortality']].copy()

    # 2. Create Hospital A (FAIR)
    # Random sample, natural distribution
    df_a = demo_df.sample(n=300, random_state=42)
    df_a.to_csv(os.path.join(base_dir, 'data', 'hospital_A_fair.csv'), index=False)

    # 3. Create Hospital B (BIASED)
    # We artificially KILL senior patients to force a bias alert
    df_b = demo_df.sample(n=300, random_state=99)
    
    def inject_bias(row):
        # If patient is senior, 85% chance they die in this specific dataset
        if row['is_senior'] == 1:
            return 1 if np.random.rand() < 0.85 else 0
        return row['mortality']

    df_b['mortality'] = df_b.apply(inject_bias, axis=1)
    df_b.to_csv(os.path.join(base_dir, 'data', 'hospital_B_biased.csv'), index=False)
    
    print("Data Preparation Complete: Hospital A (Fair) and Hospital B (Biased) created.")

if __name__ == "__main__":
    prepare_demo_data()