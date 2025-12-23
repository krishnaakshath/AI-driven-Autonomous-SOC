import pandas as pd
from pathlib import Path

# Absolute-safe dataset path
DATASET_DIR = Path("data/datasets/cicids_selected")
OUTPUT_FILE = Path("data/parsed_logs/cicids_processed.csv")

FEATURES = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "SYN Flag Count",
    "ACK Flag Count",
    "RST Flag Count",
    "Destination Port"
]

dfs = []

print(f"[INFO] Looking for CSV files in: {DATASET_DIR.resolve()}")

for file in DATASET_DIR.glob("*.csv"):
    print(f"[+] Loading {file.name}")
    df = pd.read_csv(file, low_memory=False)

    # Normalize column names
    df.columns = df.columns.str.strip()

    # Select required features
    df = df[FEATURES]
    dfs.append(df)

if not dfs:
    raise FileNotFoundError("No CSV files found — check dataset path")

final_df = pd.concat(dfs, ignore_index=True)

# Clean invalid values
final_df = final_df.replace([float("inf"), -float("inf")], None)
final_df = final_df.dropna()

# Ensure output directory exists
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
final_df.to_csv(OUTPUT_FILE, index=False)

print("[✔] CICIDS preprocessing complete")
print("[✔] Final dataset shape:", final_df.shape)

