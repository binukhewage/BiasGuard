import pandas as pd
import numpy as np
import os
import json
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold

# ==============================
# CONFIGURATION
# ==============================

# backend/utils/data_prep.py
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Raw CSVs inside backend/data/
DATA_DIR = os.path.join(BACKEND_DIR, "data")

# Federated output inside backend/data/federated/
OUTPUT_DIR = os.path.join(DATA_DIR, "federated")

os.makedirs(OUTPUT_DIR, exist_ok=True)

INTERESTING_LABS = [
    'creatinine', 'glucose', 'sodium', 'potassium',
    'hemoglobin', 'WBC x 1000', 'lactate'
]

CHUNK_SIZE = 100000
MIN_PATIENTS_THRESHOLD = 1  # You can increase later


# ==============================
# 1. LOAD PATIENT COHORT
# ==============================
def load_patient_cohort():
    print("Loading Patient Demographics (patient.csv)...")
    path = os.path.join(DATA_DIR, "patient.csv")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path, usecols=[
        'patientunitstayid', 'age', 'gender', 'ethnicity',
        'hospitalid', 'unitdischargestatus'
    ])

    df['age'] = df['age'].replace('> 89', '90')
    df['age'] = pd.to_numeric(df['age'], errors='coerce')

    df = df.dropna(subset=['patientunitstayid', 'age', 'unitdischargestatus'])

    df['mortality'] = (df['unitdischargestatus'] == 'Expired').astype(int)
    df['is_senior'] = (df['age'] > 65).astype(int)

    print(f"-> Found {len(df)} valid patients.")
    return df


# ==============================
# 2. PROCESS VITALS
# ==============================
def process_vitals(cohort_ids):
    print("Processing Vitals...")
    path = os.path.join(DATA_DIR, "vitalPeriodic.csv")

    if not os.path.exists(path):
        print("Warning: vitalPeriodic.csv not found. Skipping vitals.")
        return pd.DataFrame()

    aggregated = []

    for chunk in pd.read_csv(
        path,
        chunksize=CHUNK_SIZE,
        usecols=['patientunitstayid', 'heartrate', 'sao2', 'systemicmean']
    ):
        chunk = chunk[chunk['patientunitstayid'].isin(cohort_ids)]

        if not chunk.empty:
            stats = chunk.groupby('patientunitstayid').agg({
                'heartrate': 'mean',
                'sao2': 'min',
                'systemicmean': 'mean'
            }).reset_index()

            aggregated.append(stats)

    if aggregated:
        full = pd.concat(aggregated)
        final = full.groupby('patientunitstayid').mean().reset_index()
        final.columns = ['patientunitstayid', 'avg_heartrate', 'min_o2_sat', 'avg_bp']
        print(f"-> Vitals processed for {len(final)} patients.")
        return final

    return pd.DataFrame()


# ==============================
# 3. PROCESS LABS
# ==============================
def process_labs(cohort_ids):
    print("Processing Labs...")
    path = os.path.join(DATA_DIR, "lab.csv")

    if not os.path.exists(path):
        print("Warning: lab.csv not found. Skipping labs.")
        return pd.DataFrame()

    aggregated = []

    for chunk in pd.read_csv(
        path,
        chunksize=CHUNK_SIZE,
        usecols=['patientunitstayid', 'labname', 'labresult']
    ):
        chunk = chunk[chunk['patientunitstayid'].isin(cohort_ids)]
        chunk = chunk[chunk['labname'].isin(INTERESTING_LABS)]

        if not chunk.empty:
            pivot = (
                chunk.groupby(['patientunitstayid', 'labname'])['labresult']
                .max()
                .unstack()
            )
            aggregated.append(pivot)

    if aggregated:
        full = pd.concat(aggregated)
        final = full.groupby('patientunitstayid').max().reset_index()

        final.columns = [
            'patientunitstayid' if col == 'patientunitstayid'
            else f"max_{col.replace(' ', '_')}"
            for col in final.columns
        ]

        print(f"-> Labs processed for {len(final)} patients.")
        return final

    return pd.DataFrame()


# ==============================
# 4. MAIN PIPELINE
# ==============================
NUM_CLIENTS = 10


def main():
    patients = load_patient_cohort()
    cohort_ids = set(patients['patientunitstayid'])

    vitals = process_vitals(cohort_ids)
    labs = process_labs(cohort_ids)

    print("Merging datasets...")

    if vitals.empty:
        merged = patients.copy()
    else:
        merged = patients.merge(vitals, on='patientunitstayid', how='inner')

    if not labs.empty:
        merged = merged.merge(labs, on='patientunitstayid', how='left')

    print(f"-> Global Dataset Size: {len(merged)} patients")

    print(f"\nCreating {NUM_CLIENTS} Slightly Imbalanced Stratified Nodes...")

    merged = merged.sample(frac=1, random_state=42).reset_index(drop=True)

    # Split by mortality class
    class_0 = merged[merged['mortality'] == 0].copy()
    class_1 = merged[merged['mortality'] == 1].copy()

    # Shuffle within classes
    class_0 = class_0.sample(frac=1, random_state=42).reset_index(drop=True)
    class_1 = class_1.sample(frac=1, random_state=42).reset_index(drop=True)

    # Create slightly uneven proportions
    rng = np.random.default_rng(42)
    proportions = rng.uniform(0.8, 1.2, NUM_CLIENTS)
    proportions = proportions / proportions.sum()

    client_registry = []

    start_0 = 0
    start_1 = 0

    for i in range(NUM_CLIENTS):

        prop = proportions[i]

        size_0 = int(len(class_0) * prop)
        size_1 = int(len(class_1) * prop)

        end_0 = start_0 + size_0
        end_1 = start_1 + size_1

        client_data = pd.concat([
            class_0.iloc[start_0:end_0],
            class_1.iloc[start_1:end_1]
        ])

        start_0 = end_0
        start_1 = end_1

        client_data = client_data.sample(frac=1, random_state=42).reset_index(drop=True)

        client_name = f"client_{i+1}"
        filename = f"{client_name}.csv"
        output_path = os.path.join(OUTPUT_DIR, filename)

        # Local imputation
        numeric_cols = client_data.select_dtypes(include=np.number).columns
        cols_to_impute = [
            c for c in numeric_cols
            if c not in ['patientunitstayid', 'mortality', 'is_senior', 'hospitalid']
        ]

        if cols_to_impute:
            valid_cols = [
                c for c in cols_to_impute
                if client_data[c].notna().sum() > 0
            ]

            if valid_cols:
                imputer = SimpleImputer(strategy="median")
                client_data[valid_cols] = imputer.fit_transform(
                    client_data[valid_cols]
                )

        client_data.to_csv(output_path, index=False)

        client_registry.append({
            "id": str(i+1),
            "name": client_name,
            "file": filename,
            "sample_size": len(client_data)
        })

        print(f"   [+] Generated {client_name} (n={len(client_data)})")

    registry_path = os.path.join(OUTPUT_DIR, "client_registry.json")
    with open(registry_path, 'w') as f:
        json.dump(client_registry, f, indent=4)

    print(f"\nSUCCESS ✅ Federated network created with {NUM_CLIENTS} nodes.")
    print(f"Saved inside: {OUTPUT_DIR}")



if __name__ == "__main__":
    main()
