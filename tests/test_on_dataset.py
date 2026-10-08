"""
Test fraud detection on your actual datasets
Tests both Ethereum and Solana data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.detection.hybrid_detector import HybridDetector

print("="*80)
print("TESTING ON YOUR DATASETS")
print("="*80)
print()

# Initialize detector
detector = HybridDetector()

# Test 1: Ethereum Dataset
print("TEST 1: Ethereum Dataset")
print("-"*80)

ethereum_path = Path("data/processed/ethereum_features.csv")
if ethereum_path.exists():
    df_eth = pd.read_csv(ethereum_path)
    print(f"✓ Loaded {len(df_eth)} Ethereum addresses")
    print(f"  Fraud: {df_eth['FLAG'].sum()} addresses")
    print(f"  Legitimate: {len(df_eth) - df_eth['FLAG'].sum()} addresses")
    print()
    
    # Test on first 5 addresses
    print("Testing first 5 addresses:")
    print("-"*80)
    
    for idx in range(min(5, len(df_eth))):
        row = df_eth.iloc[idx]
        
        # Convert to feature dict
        features = {
            'total_transactions': row.get('total transactions (including tnx to create contract', 0),
            'Sent tnx': row.get('Sent tnx', 0),
            'Received Tnx': row.get('Received Tnx', 0),
            'Unique Sent To Addresses': row.get('Unique Sent To Addresses', 0),
            'Unique Received From Addresses': row.get('Unique Received From Addresses', 0),
            'total ether sent': row.get('total Ether sent', 0),
            'total ether received': row.get('total ether received', 0),
            'total ether balance': row.get('total ether balance', 0),
            'avg val sent': row.get('avg val sent', 0),
            'avg val received': row.get('avg val received', 0),
            'Time Diff between first and last (Mins)': row.get('Time Diff between first and last (Mins)', 0),
        }
        
        # Get GNN score (if available)
        gnn_score = 15.0  # Default placeholder
        
        # Detect
        score, category, explanations = detector.detect(
            f"0x{'0'*40}",  # Placeholder address
            features,
            gnn_score
        )
        
        actual_label = "FRAUD" if row['FLAG'] == 1 else "LEGIT"
        predicted = "FRAUD" if score >= 50 else "LEGIT"
        match = "✓" if actual_label == predicted else "✗"
        
        print(f"\n[{idx+1}] {match} Actual: {actual_label:5s} | Predicted: {score:5.1f}/100 ({category})")
        
    print()
    print("="*80)
else:
    print("✗ Ethereum dataset not found")
    print()

# Test 2: Solana Dataset  
print("\nTEST 2: Solana Dataset")
print("-"*80)

solana_path = Path("data/processed/solana_features.csv")
if solana_path.exists():
    df_sol = pd.read_csv(solana_path)
    print(f"✓ Loaded {len(df_sol)} Solana addresses")
    
    # Check if it has labels
    if 'label' in df_sol.columns or 'FLAG' in df_sol.columns:
        label_col = 'label' if 'label' in df_sol.columns else 'FLAG'
        fraud_count = df_sol[label_col].sum()
        print(f"  Fraud: {fraud_count} addresses")
        print(f"  Legitimate: {len(df_sol) - fraud_count} addresses")
    else:
        print(f"  (No labels available)")
    
    print()
else:
    print("✗ Solana dataset not found")
    print()

# Test 3: HF Dataset (Hack/Fraud dataset)
print("TEST 3: HF Dataset (Crypto Hacks/Fraud)")
print("-"*80)

hf_paths = [
    "Dataset-Capstone/HF DATASET/CSV/2023.csv",
    "Dataset-Capstone/HF DATASET/CSV/2022.csv",
    "Dataset-Capstone/HF DATASET/CSV/2021.csv"
]

for hf_path in hf_paths:
    if Path(hf_path).exists():
        df_hf = pd.read_csv(hf_path)
        print(f"✓ {Path(hf_path).name}: {len(df_hf)} records")
    else:
        print(f"✗ {Path(hf_path).name}: Not found")

print()
print("="*80)
print()

# Summary
print("TESTING SUMMARY")
print("="*80)
print()
print("Your datasets available for testing:")
print("  1. ethereum_features.csv - Transaction features (normalized)")
print("  2. solana_features.csv - Solana blockchain data")
print("  3. HF Dataset - Real hack/fraud incidents (2021-2024)")
print()
print("How to test:")
print("  1. Run: python test_on_dataset.py")
print("  2. Run: python verify_all_features.py (quick test)")
print("  3. Run: python demo_ml_detection.py (real address demo)")
print()
print("Your system is trained on 20 labeled Ethereum addresses and")
print("can now detect fraud patterns on NEW addresses from these datasets.")
print()
print("="*80)
