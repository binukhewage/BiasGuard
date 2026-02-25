import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split, StratifiedKFold

# =============================
# CONFIGURATION
# =============================

# backend/data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = BASE_DIR

RAW_DIR = os.path.join(DATA_DIR, "raw")
FED_DIR = os.path.join(DATA_DIR, "federated")
CLIENT11_DIR = os.path.join(DATA_DIR, "client11")

os.makedirs(FED_DIR, exist_ok=True)
os.makedirs(CLIENT11_DIR, exist_ok=True)

NUM_CLIENTS = 10
HOLDOUT_RATIO = 0.15
RANDOM_STATE = 42

INTERESTING_LABS = [
    'creatinine',
    'glucose',
    'sodium',
    'potassium',
    'hemoglobin',
    'WBC x 1000',
    'lactate'
]

# =============================
# LOAD PATIENT DATA
# =============================

def load_patients():
    print("Loading patient.csv...")
    path = os.path.join(RAW_DIR, "patient.csv")
    df = pd.read_csv(path)

    # Clean age
    df['age'] = df['age'].replace('> 89', '90')
    df['age'] = pd.to_numeric(df['age'], errors='coerce')

    # Keep required columns
    df = df.dropna(subset=['patientunitstayid', 'age', 'unitdischargestatus'])

    # Create target
    df['mortality'] = (df['unitdischargestatus'] == 'Expired').astype(int)

    # Fairness attribute
    df['is_senior'] = (df['age'] > 65).astype(int)

    return df[['patientunitstayid', 'age', 'hospitalid', 'mortality', 'is_senior']]

# =============================
# PROCESS VITALS
# =============================

def process_vitals():
    print("Processing vitalPeriodic.csv...")
    path = os.path.join(RAW_DIR, "vitalPeriodic.csv")
    df = pd.read_csv(path)

    agg = df.groupby('patientunitstayid').agg({
        'heartrate': 'mean',
        'sao2': 'min',
        'systemicmean': 'mean'
    }).reset_index()

    agg.columns = [
        'patientunitstayid',
        'avg_heartrate',
        'min_o2_sat',
        'avg_bp'
    ]

    return agg

# =============================
# PROCESS LABS
# =============================

def process_labs():
    print("Processing lab.csv...")
    path = os.path.join(RAW_DIR, "lab.csv")
    df = pd.read_csv(path)

    df = df[df['labname'].isin(INTERESTING_LABS)]

    pivot = (
        df.groupby(['patientunitstayid', 'labname'])['labresult']
        .max()
        .unstack()
        .reset_index()
    )

    pivot.columns = [
        'patientunitstayid' if col == 'patientunitstayid'
        else f"max_{col.replace(' ', '_')}"
        for col in pivot.columns
    ]

    return pivot

# =============================
# MAIN PIPELINE
# =============================

def main():

    print("Loading datasets...")

    patients = load_patients()
    vitals = process_vitals()
    labs = process_labs()

    print("Merging datasets...")

    # LEFT joins to preserve all patients
    df = patients.merge(vitals, on='patientunitstayid', how='left')
    df = df.merge(labs, on='patientunitstayid', how='left')

    print(f"Final merged dataset size: {len(df)}")

    # =============================
    # HOLD OUT 15% (Client 11)
    # =============================

    train_df, client11_df = train_test_split(
        df,
        test_size=HOLDOUT_RATIO,
        stratify=df['mortality'],
        random_state=RANDOM_STATE
    )

    client11_path = os.path.join(CLIENT11_DIR, "new_hospital.csv")
    client11_df.to_csv(client11_path, index=False)

    print(f"Client 11 size: {len(client11_df)}")

    # =============================
    # SPLIT REMAINING INTO 10 CLIENTS
    # =============================

    print("Creating 10 stratified federated clients...")

    skf = StratifiedKFold(
        n_splits=NUM_CLIENTS,
        shuffle=True,
        random_state=RANDOM_STATE
    )

    X = train_df.drop(columns=['mortality'])
    y = train_df['mortality']

    for i, (_, idx) in enumerate(skf.split(X, y)):
        client_data = train_df.iloc[idx].copy()

        client_path = os.path.join(FED_DIR, f"client_{i+1}.csv")
        client_data.to_csv(client_path, index=False)

        print(f"Saved client_{i+1}.csv (n={len(client_data)})")

        

    print("\nMortality Distribution:")
    print(df['mortality'].value_counts())

    print("\nMortality Ratio:")
    print(df['mortality'].value_counts(normalize=True))

    print("Data preparation complete.")
    


if __name__ == "__main__":
    main()