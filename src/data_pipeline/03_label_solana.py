"""
STEP 3: Label Solana Rug-Pulls
Apply heuristic rule to identify rug-pull patterns in Solana liquidity pools

Rug-pull criteria:
1. REMOVE_RATIO >= 0.85 (removed ≥85% of added liquidity)
2. INACTIVITY_STATUS == 'Inactive' (no recent activity)
3. NUM_LIQUIDITY_ADDS <= 3 (very few liquidity providers)

This combination indicates: creators added liquidity, removed most of it, and abandoned the pool
"""

import pandas as pd
import numpy as np

def label_rugpulls(input_path='data/processed/solana_clean.csv', 
                   output_path='data/processed/solana_labeled.csv'):
    """
    Apply rug-pull labeling rule to cleaned Solana data
    """
    print("="*80)
    print("STEP 3: LABELING SOLANA RUG-PULLS")
    print("="*80)
    
    # Load cleaned data
    df = pd.read_csv(input_path)
    print(f"\nLoaded data: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Verify required columns exist
    required_base_cols = ['TOTAL_ADDED_LIQUIDITY', 'TOTAL_REMOVED_LIQUIDITY', 
                          'INACTIVITY_STATUS', 'NUM_LIQUIDITY_ADDS']
    missing = [col for col in required_base_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Compute REMOVE_RATIO if not present
    if 'REMOVE_RATIO' not in df.columns:
        print("\nComputing REMOVE_RATIO...")
        df['REMOVE_RATIO'] = df.apply(
            lambda row: min(row['TOTAL_REMOVED_LIQUIDITY'] / row['TOTAL_ADDED_LIQUIDITY'], 10.0) 
            if row['TOTAL_ADDED_LIQUIDITY'] > 0 else 0.0,
            axis=1
        )
        print(f"  Added REMOVE_RATIO column")
    
    # Compute POOL_LIFETIME_HOURS if not present
    if 'POOL_LIFETIME_HOURS' not in df.columns:
        if 'FIRST_POOL_ACTIVITY_TIMESTAMP' in df.columns and 'LAST_POOL_ACTIVITY_TIMESTAMP' in df.columns:
            print("\nComputing POOL_LIFETIME_HOURS...")
            df['FIRST_POOL_ACTIVITY_TIMESTAMP'] = pd.to_datetime(df['FIRST_POOL_ACTIVITY_TIMESTAMP'])
            df['LAST_POOL_ACTIVITY_TIMESTAMP'] = pd.to_datetime(df['LAST_POOL_ACTIVITY_TIMESTAMP'])
            df['POOL_LIFETIME_HOURS'] = (
                df['LAST_POOL_ACTIVITY_TIMESTAMP'] - df['FIRST_POOL_ACTIVITY_TIMESTAMP']
            ).dt.total_seconds() / 3600
            print(f"  Added POOL_LIFETIME_HOURS column")
    
    print(f"\n{'='*80}")
    print("APPLYING RUG-PULL RULE")
    print(f"{'='*80}")
    
    # Define rug-pull rule
    print("\nRule: (REMOVE_RATIO >= 0.85) AND (INACTIVITY_STATUS == 'Inactive') AND (NUM_LIQUIDITY_ADDS <= 3)")
    
    # Apply rule
    is_rugpull = (
        (df['REMOVE_RATIO'] >= 0.85) & 
        (df['INACTIVITY_STATUS'] == 'Inactive') & 
        (df['NUM_LIQUIDITY_ADDS'] <= 3)
    )
    
    # Add label column
    df['IS_RUGPULL'] = is_rugpull.astype(int)
    
    # Statistics
    rugpull_count = df['IS_RUGPULL'].sum()
    legit_count = len(df) - rugpull_count
    rugpull_pct = (rugpull_count / len(df)) * 100
    
    print(f"\nLabeling results:")
    print(f"  Total pools: {len(df):,}")
    print(f"  Rug-pulls (IS_RUGPULL=1): {rugpull_count:,} ({rugpull_pct:.2f}%)")
    print(f"  Legitimate (IS_RUGPULL=0): {legit_count:,} ({100-rugpull_pct:.2f}%)")
    
    # Analyze rug-pull characteristics
    rugpulls = df[df['IS_RUGPULL'] == 1]
    
    print(f"\n{'='*80}")
    print("RUG-PULL STATISTICS")
    print(f"{'='*80}")
    
    print(f"\nREMOVE_RATIO (rug-pulls):")
    print(f"  Min: {rugpulls['REMOVE_RATIO'].min():.4f}")
    print(f"  Mean: {rugpulls['REMOVE_RATIO'].mean():.4f}")
    print(f"  Max: {rugpulls['REMOVE_RATIO'].max():.4f}")
    
    print(f"\nNUM_LIQUIDITY_ADDS (rug-pulls):")
    print(f"  Min: {rugpulls['NUM_LIQUIDITY_ADDS'].min():.0f}")
    print(f"  Mean: {rugpulls['NUM_LIQUIDITY_ADDS'].mean():.2f}")
    print(f"  Max: {rugpulls['NUM_LIQUIDITY_ADDS'].max():.0f}")
    
    print(f"\nPOOL_LIFETIME_HOURS (rug-pulls):")
    if 'POOL_LIFETIME_HOURS' in df.columns:
        print(f"  Mean: {rugpulls['POOL_LIFETIME_HOURS'].mean():.2f} hours")
        print(f"  Median: {rugpulls['POOL_LIFETIME_HOURS'].median():.2f} hours")
    
    # Verification
    print(f"\n{'='*80}")
    print("VERIFICATION")
    print(f"{'='*80}")
    
    print(f"\nAll rug-pulls have REMOVE_RATIO >= 0.85: {(rugpulls['REMOVE_RATIO'] >= 0.85).all()}")
    print(f"All rug-pulls have INACTIVITY_STATUS == 'Inactive': {(rugpulls['INACTIVITY_STATUS'] == 'Inactive').all()}")
    print(f"All rug-pulls have NUM_LIQUIDITY_ADDS <= 3: {(rugpulls['NUM_LIQUIDITY_ADDS'] <= 3).all()}")
    
    # Save labeled data
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved labeled data: {output_path}")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {df.columns.tolist()}")
    
    return df


if __name__ == "__main__":
    # Label rug-pulls
    labeled_df = label_rugpulls()
    
    print(f"\n{'='*80}")
    print("✅ STEP 3 COMPLETE - Solana rug-pulls labeled")
    print(f"{'='*80}")
    print(f"\nExpected output: 105,777 legitimate + 10,527 rug-pulls = 116,304 total")
    print(f"Actual output: {len(labeled_df):,} total")
    print(f"  Legitimate: {(labeled_df['IS_RUGPULL'] == 0).sum():,}")
    print(f"  Rug-pulls: {(labeled_df['IS_RUGPULL'] == 1).sum():,}")
