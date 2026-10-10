"""
Download Public Ethereum Fraud Datasets
Sources:
1. Real-CATS: 12,561 fraud + 15,595 legit (Kaggle)
2. Poison-Hunter: 5,890 phishing addresses (GitHub)
3. Kaggle Ethereum Fraud: 9,841 transactions (Kaggle)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import pandas as pd
from tqdm import tqdm
import time

print("="*80)
print("📥 DOWNLOADING PUBLIC ETHEREUM FRAUD DATASETS")
print("="*80)
print("Target: 5000 fraud + 5000 legit addresses")
print("="*80)

all_addresses = []
seen = set()

def add_address(address, label, source, confidence=1.0, name=''):
    """Add unique address"""
    address = address.lower().strip()
    if not address.startswith('0x') or len(address) != 42:
        return False
    if address in seen:
        return False
    seen.add(address)
    all_addresses.append({
        'address': address,
        'label': label,
        'source': source,
        'confidence': confidence,
        'name': name
    })
    return True

# ============================================================================
# SOURCE 1: Poison-Hunter GitHub (5,890 phishing addresses)
# ============================================================================

print("\n[1/4] Poison-Hunter Dataset (GitHub)...")
print("Target: ~5,890 phishing addresses")

try:
    # Download phishing addresses
    url = "https://raw.githubusercontent.com/DS2L/Poison-Hunter/main/phishing_address_groundtruth.txt"
    
    print(f"  Downloading from: {url}")
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        lines = response.text.strip().split('\n')
        count = 0
        
        for line in tqdm(lines, desc="Poison-Hunter"):
            line = line.strip()
            if line and line.startswith('0x'):
                if add_address(line, 1, 'poison_hunter', 1.0, 'Phishing Address'):
                    count += 1
        
        print(f"  ✓ Collected: {count} phishing addresses")
    else:
        print(f"  ✗ Failed: HTTP {response.status_code}")

except Exception as e:
    print(f"  ✗ Error: {e}")

# Download benign addresses
try:
    url = "https://raw.githubusercontent.com/DS2L/Poison-Hunter/main/popular_address.txt"
    
    print(f"\n  Downloading benign addresses...")
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        lines = response.text.strip().split('\n')
        count = 0
        
        for line in tqdm(lines, desc="Benign"):
            line = line.strip()
            if line and line.startswith('0x'):
                if add_address(line, 0, 'poison_hunter', 1.0, 'Popular Address'):
                    count += 1
        
        print(f"  ✓ Collected: {count} benign addresses")
    else:
        print(f"  ✗ Failed: HTTP {response.status_code}")

except Exception as e:
    print(f"  ✗ Error: {e}")

print(f"\n✓ Poison-Hunter Total: {len([a for a in all_addresses if a['source'] == 'poison_hunter'])} addresses")

# ============================================================================
# SOURCE 2: Real-CATS Dataset (Need manual download from Kaggle)
# ============================================================================

print("\n[2/4] Real-CATS Dataset (Kaggle)...")
print("Note: This dataset requires manual download from Kaggle")
print("URL: https://www.kaggle.com/datasets/lvd312393/real-cats")
print("")
print("Instructions:")
print("1. Go to https://www.kaggle.com/datasets/lvd312393/real-cats")
print("2. Download 'CE.tsv' (12,561 criminal Ethereum addresses)")
print("3. Download 'BE.tsv' (15,595 benign Ethereum addresses)")
print("4. Place files in: data/raw/")
print("")

# Check if files exist
ce_path = 'data/raw/CE.tsv'
be_path = 'data/raw/BE.tsv'

if os.path.exists(ce_path):
    print("  ✓ Found CE.tsv, loading criminal addresses...")
    try:
        df = pd.read_csv(ce_path, sep='\t')
        if 'Address' in df.columns:
            for addr in tqdm(df['Address'], desc="Real-CATS Criminal"):
                add_address(addr, 1, 'real_cats', 1.0, 'Criminal Address')
        print(f"  ✓ Loaded: {len(df)} criminal addresses")
    except Exception as e:
        print(f"  ✗ Error loading CE.tsv: {e}")
else:
    print(f"  ⚠️ CE.tsv not found at: {ce_path}")
    print(f"     Download from: https://www.kaggle.com/datasets/lvd312393/real-cats")

if os.path.exists(be_path):
    print("  ✓ Found BE.tsv, loading benign addresses...")
    try:
        df = pd.read_csv(be_path, sep='\t')
        if 'Address' in df.columns:
            for addr in tqdm(df['Address'], desc="Real-CATS Benign"):
                add_address(addr, 0, 'real_cats', 1.0, 'Benign Address')
        print(f"  ✓ Loaded: {len(df)} benign addresses")
    except Exception as e:
        print(f"  ✗ Error loading BE.tsv: {e}")
else:
    print(f"  ⚠️ BE.tsv not found at: {be_path}")
    print(f"     Download from: https://www.kaggle.com/datasets/lvd312393/real-cats")

# ============================================================================
# SOURCE 3: Ethereum Fraud Detection (Kaggle) - Addresses only
# ============================================================================

print("\n[3/4] Ethereum Fraud Detection Dataset (Kaggle)...")
print("Note: This dataset also requires manual download")
print("URL: https://www.kaggle.com/datasets/vagifa/ethereum-frauddetection-dataset")
print("")
print("Instructions:")
print("1. Go to: https://www.kaggle.com/datasets/vagifa/ethereum-frauddetection-dataset")
print("2. Download 'transaction_dataset.csv'")
print("3. Place in: data/raw/")
print("")

fraud_dataset_path = 'data/raw/transaction_dataset.csv'

if os.path.exists(fraud_dataset_path):
    print("  ✓ Found transaction_dataset.csv, extracting addresses...")
    try:
        df = pd.read_csv(fraud_dataset_path)
        
        # Extract unique addresses from 'from' and 'to' columns
        if 'FLAG' in df.columns:
            # Fraud transactions
            fraud_tx = df[df['FLAG'] == 1]
            
            if 'Address' in df.columns:
                for addr in tqdm(fraud_tx['Address'].unique(), desc="Fraud addresses"):
                    add_address(addr, 1, 'kaggle_fraud_dataset', 0.9)
            
            # Legit transactions
            legit_tx = df[df['FLAG'] == 0]
            
            if 'Address' in df.columns:
                for addr in tqdm(legit_tx['Address'].unique(), desc="Legit addresses"):
                    add_address(addr, 0, 'kaggle_fraud_dataset', 0.9)
        
        print(f"  ✓ Extracted addresses from Kaggle fraud dataset")
    except Exception as e:
        print(f"  ✗ Error: {e}")
else:
    print(f"  ⚠️ transaction_dataset.csv not found")

# ============================================================================
# SOURCE 4: Combine with existing data
# ============================================================================

print("\n[4/4] Combining with existing collected data...")

try:
    existing = pd.read_csv('data/training_collected/combined_dataset.csv')
    
    for _, row in tqdm(existing.iterrows(), total=len(existing), desc="Existing"):
        add_address(
            row['address'],
            row['label'],
            row['source'],
            row['confidence'],
            row.get('name', '')
        )
    
    print(f"  ✓ Added {len(existing)} existing addresses")
except Exception as e:
    print(f"  No existing data: {e}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*80)
print("📊 DATASET COLLECTION COMPLETE!")
print("="*80)

df = pd.DataFrame(all_addresses)

fraud_count = (df['label'] == 1).sum()
legit_count = (df['label'] == 0).sum()

print(f"\n🚨 FRAUD ADDRESSES: {fraud_count}")
print(f"✅ LEGITIMATE ADDRESSES: {legit_count}")
print(f"📈 TOTAL: {len(df)}")

# Source breakdown
print(f"\n📋 SOURCES:")
for source, count in df['source'].value_counts().items():
    fraud_in_source = ((df['source'] == source) & (df['label'] == 1)).sum()
    legit_in_source = ((df['source'] == source) & (df['label'] == 0)).sum()
    print(f"   {source:30s} {count:6d} (F:{fraud_in_source:5d}, L:{legit_in_source:5d})")

# Save
output_path = 'data/training_collected/final_dataset.csv'
df.to_csv(output_path, index=False)

print(f"\n💾 Saved to: {output_path}")

# Recommendations
print(f"\n💡 NEXT STEPS:")
print("="*80)

if fraud_count >= 5000 and legit_count >= 5000:
    print("✅ EXCELLENT! You have 5000+ of each class!")
    print("   Ready for strong GNN training!")
    print("   Run: python scripts/build_3hop_graph.py")
elif fraud_count >= 1000 and legit_count >= 1000:
    print("✅ GOOD! You have 1000+ of each class")
    print("   Can train decent GNN model")
    print("   For better results, download Real-CATS from Kaggle:")
    print("   https://www.kaggle.com/datasets/lvd312393/real-cats")
elif fraud_count >= 100:
    print("⚠️ Workable but limited")
    print("   Current: {} fraud, {} legit".format(fraud_count, legit_count))
    print("   ")
    print("   TO GET 5000+ ADDRESSES:")
    print("   1. Download Real-CATS from Kaggle (12,561 fraud + 15,595 legit)")
    print("      URL: https://www.kaggle.com/datasets/lvd312393/real-cats")
    print("   2. Place CE.tsv and BE.tsv in data/raw/")
    print("   3. Re-run this script")
else:
    print("❌ Not enough data")
    print("   REQUIRED: Download Real-CATS dataset from Kaggle")
    print("   URL: https://www.kaggle.com/datasets/lvd312393/real-cats")

print("="*80)
