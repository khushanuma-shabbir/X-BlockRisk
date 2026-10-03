"""
REPRODUCIBLE ETHEREUM DATA PREPROCESSING PIPELINE

This script replaces the missing ethereum_clean.csv step.

Pipeline:
1. Load raw Kaggle data
2. Select 38 feature columns + FLAG + Address
3. Fill numeric NaN with 0 (ERC20 columns)
4. Remove exact duplicates over features + FLAG
5. Report label conflicts (same features, different labels)
6. Stratified 80/20 train/test split (seed=42)
7. Save to data/splits/ethereum/ with Address and FLAG

Author: Capstone Project
Date: 2026-10-04
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os

print("="*80)
print("ETHEREUM DATA PREPROCESSING PIPELINE")
print("="*80)

# Step 1: Load raw Kaggle data
print("\n[1/7] Loading raw Kaggle dataset...")
df_raw = pd.read_csv('Dataset-Capstone/transaction_dataset.csv')
print(f"  Loaded: {len(df_raw):,} rows, {len(df_raw.columns)} columns")
print(f"  Fraud: {(df_raw['FLAG']==1).sum():,}, Legit: {(df_raw['FLAG']==0).sum():,}")

# Step 2: Select feature columns
print("\n[2/7] Selecting 38 feature columns + FLAG + Address...")

# Feature columns matching config/feature_columns.py
selected_features = [
    'Avg min between sent tnx',
    'Avg min between received tnx',
    'Time Diff between first and last (Mins)',
    'Sent tnx',
    'Received Tnx',
    'Number of Created Contracts',
    'Unique Received From Addresses',
    'Unique Sent To Addresses',
    'min value received',
    'max value received',
    'avg val received',
    'min val sent',
    'max val sent',
    'avg val sent',
    'min value sent to contract',
    'max val sent to contract',
    'avg value sent to contract',
    'total transactions (including tnx to create contract',
    'total Ether sent',
    'total ether received',
    'total ether sent contracts',
    'total ether balance',
    'Total ERC20 tnxs',
    'ERC20 total Ether received',
    'ERC20 total ether sent',
    'ERC20 total Ether sent contract',
    'ERC20 uniq sent addr',
    'ERC20 uniq rec addr',
    'ERC20 uniq sent addr.1',
    'ERC20 uniq rec contract addr',
    'ERC20 min val rec',
    'ERC20 max val rec',
    'ERC20 avg val rec',
    'ERC20 min val sent',
    'ERC20 max val sent',
    'ERC20 avg val sent',
    'ERC20 uniq sent token name',
    'ERC20 uniq rec token name'
]

# Map Kaggle columns (handle leading/trailing whitespace)
kaggle_col_map = {}
for feat in selected_features:
    matching = [col for col in df_raw.columns if col.strip() == feat]
    if matching:
        kaggle_col_map[feat] = matching[0]
    else:
        raise ValueError(f"Feature not found in Kaggle data: {feat}")

print(f"  Mapped {len(kaggle_col_map)} features successfully")

# Create clean dataframe
df = df_raw[['Address', 'FLAG'] + list(kaggle_col_map.values())].copy()
df.columns = ['Address', 'FLAG'] + selected_features

print(f"  Shape: {df.shape}")

# Step 3: Fill NaN with 0
print("\n[3/7] Filling numeric NaN with 0...")
nan_before = df[selected_features].isnull().sum().sum()
df[selected_features] = df[selected_features].fillna(0)
nan_after = df[selected_features].isnull().sum().sum()
print(f"  Filled {nan_before:,} NaN values")
print(f"  Remaining NaN: {nan_after}")

# Step 4: Remove exact duplicates
print("\n[4/7] Removing exact duplicates over features + FLAG...")
print(f"  Before dedup: {len(df):,} rows")

# Identify duplicates before dropping
duplicates = df.duplicated(subset=selected_features + ['FLAG'], keep=False)
duplicate_groups = df[duplicates].groupby(selected_features + ['FLAG']).size()
print(f"  Found {duplicates.sum():,} duplicate rows in {len(duplicate_groups):,} groups")

df_dedup = df.drop_duplicates(subset=selected_features + ['FLAG'], keep='first')
dropped_count = len(df) - len(df_dedup)
dropped_fraud = (df['FLAG']==1).sum() - (df_dedup['FLAG']==1).sum()
dropped_legit = (df['FLAG']==0).sum() - (df_dedup['FLAG']==0).sum()

print(f"  After dedup: {len(df_dedup):,} rows")
print(f"  Dropped: {dropped_count} exact duplicates ({dropped_fraud} fraud, {dropped_legit} legit)")

# Step 5: Check for label conflicts
print("\n[5/7] Checking for label conflicts...")
# Group by features only (ignoring FLAG) and check if multiple labels exist
feature_groups = df_dedup.groupby(selected_features)['FLAG'].apply(lambda x: x.unique())
conflicts = feature_groups[feature_groups.apply(len) > 1]

if len(conflicts) > 0:
    print(f"  ⚠️  WARNING: {len(conflicts)} feature vectors appear with BOTH labels!")
    print(f"  These {len(conflicts)} feature profiles have conflicting labels in the dataset.")
    print(f"  Keeping both instances (not dropping).")
else:
    print(f"  ✓ No label conflicts found")

# Step 6: Stratified train/test split
print("\n[6/7] Creating stratified 80/20 train/test split (seed=42)...")

train_df, test_df = train_test_split(
    df_dedup,
    test_size=0.2,
    random_state=42,
    stratify=df_dedup['FLAG']
)

print(f"  Train: {len(train_df):,} rows ({(train_df['FLAG']==1).sum():,} fraud, {(train_df['FLAG']==0).sum():,} legit)")
print(f"  Test:  {len(test_df):,} rows ({(test_df['FLAG']==1).sum():,} fraud, {(test_df['FLAG']==0).sum():,} legit)")

# Verify stratification
train_fraud_pct = (train_df['FLAG']==1).sum() / len(train_df) * 100
test_fraud_pct = (test_df['FLAG']==1).sum() / len(test_df) * 100
print(f"  Train fraud %: {train_fraud_pct:.2f}%")
print(f"  Test fraud %: {test_fraud_pct:.2f}%")

# Step 7: Save splits
print("\n[7/7] Saving train/test splits...")
output_dir = 'data/splits/ethereum'
os.makedirs(output_dir, exist_ok=True)

train_path = f'{output_dir}/train.csv'
test_path = f'{output_dir}/test.csv'

train_df.to_csv(train_path, index=False)
test_df.to_csv(test_path, index=False)

print(f"  ✓ Saved train: {train_path}")
print(f"  ✓ Saved test: {test_path}")

# Summary
print("\n" + "="*80)
print("PREPROCESSING COMPLETE")
print("="*80)
print(f"\nPipeline steps:")
print(f"  1. Loaded raw data: 9,841 rows")
print(f"  2. Selected 38 features + FLAG + Address")
print(f"  3. Filled {nan_before:,} NaN values with 0")
print(f"  4. Removed {dropped_count} exact duplicates")
print(f"  5. Label conflicts: {len(conflicts) if len(conflicts) > 0 else 0}")
print(f"  6. Split 80/20 stratified (seed=42)")
print(f"  7. Saved with Address and FLAG columns")

print(f"\nFinal dataset:")
print(f"  Train: {len(train_df):,} rows")
print(f"  Test:  {len(test_df):,} rows")
print(f"  Total: {len(df_dedup):,} rows (unique)")

print(f"\n✓ Ready for augmentation (train only) and graph construction")
