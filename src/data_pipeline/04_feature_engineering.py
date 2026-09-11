"""
STEP 4: FEATURE ENGINEERING
Prepare final feature sets for model training.

For Ethereum: Keep all behavioral numeric features (already well-engineered)
For Solana: Select key behavioral features related to rug-pull detection

Both datasets will be standardized using StandardScaler to ensure features
are on the same scale for ML algorithms.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path

def engineer_ethereum_features():
    """Prepare Ethereum features for modeling"""
    print("="*80)
    print("ETHEREUM FEATURE ENGINEERING")
    print("="*80)
    
    # Load cleaned data
    df = pd.read_csv('ethereum_clean.csv')
    print(f"\nLoaded: {len(df):,} rows, {df.shape[1]} columns")
    
    # Separate features and target
    target_col = 'FLAG'
    feature_cols = [col for col in df.columns if col != target_col]
    
    X = df[feature_cols]
    y = df[target_col]
    
    print(f"\nFeatures: {len(feature_cols)} columns")
    print(f"Target: {target_col}")
    print(f"  Class 0 (Legitimate): {(y == 0).sum():,} ({(y == 0).sum()/len(y)*100:.2f}%)")
    print(f"  Class 1 (Fraud): {(y == 1).sum():,} ({(y == 1).sum()/len(y)*100:.2f}%)")
    
    # Display sample feature names
    print(f"\nSample features (first 10):")
    for i, col in enumerate(feature_cols[:10], 1):
        print(f"  {i}. {col}")
    print(f"  ... and {len(feature_cols) - 10} more")
    
    # Apply StandardScaler
    print(f"\n✓ Applying StandardScaler to all {len(feature_cols)} features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Convert back to DataFrame for easier handling
    X_scaled_df = pd.DataFrame(X_scaled, columns=feature_cols)
    
    # Create final dataset with scaled features + target
    final_df = pd.concat([X_scaled_df, y.reset_index(drop=True)], axis=1)
    
    print(f"   Scaled feature stats (mean should be ~0, std should be ~1):")
    print(f"   - Mean of means: {X_scaled_df.mean().mean():.6f}")
    print(f"   - Mean of stds: {X_scaled_df.std().mean():.6f}")
    
    # Save scaler
    Path('scalers').mkdir(exist_ok=True)
    with open('scalers/ethereum_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print(f"\n✓ Saved scaler to: scalers/ethereum_scaler.pkl")
    
    # Save final features
    final_df.to_csv('ethereum_features.csv', index=False)
    print(f"✓ Saved features to: ethereum_features.csv")
    print(f"  Shape: {final_df.shape[0]:,} rows × {final_df.shape[1]} columns (features + FLAG)")
    
    return final_df, feature_cols


def engineer_solana_features():
    """Prepare Solana features for modeling"""
    print("\n" + "="*80)
    print("SOLANA FEATURE ENGINEERING")
    print("="*80)
    
    # Load labeled data
    df = pd.read_csv('solana_labeled.csv', parse_dates=[
        'FIRST_POOL_ACTIVITY_TIMESTAMP',
        'LAST_POOL_ACTIVITY_TIMESTAMP',
        'LAST_SWAP_TIMESTAMP'
    ])
    print(f"\nLoaded: {len(df):,} rows, {df.shape[1]} columns")
    
    # Define final feature set for rug-pull detection
    feature_cols = [
        'REMOVE_RATIO',                # Engineered in labeling step
        'NUM_LIQUIDITY_ADDS',          # How many times liquidity was added
        'NUM_LIQUIDITY_REMOVES',       # How many times liquidity was removed
        'TOTAL_ADDED_LIQUIDITY',       # Total amount added
        'TOTAL_REMOVED_LIQUIDITY',     # Total amount removed
        'POOL_LIFETIME_HOURS',         # Engineered in labeling step
        'ADD_TO_REMOVE_RATIO'          # Original ratio feature
    ]
    
    target_col = 'IS_RUGPULL'
    
    # Verify all features exist
    missing_features = [col for col in feature_cols if col not in df.columns]
    if missing_features:
        raise ValueError(f"Missing features: {missing_features}")
    
    print(f"\nSelected features: {len(feature_cols)}")
    for i, col in enumerate(feature_cols, 1):
        print(f"  {i}. {col}")
    
    # Extract features and target
    X = df[feature_cols]
    y = df[target_col]
    
    print(f"\nTarget: {target_col}")
    print(f"  Class 0 (Legitimate): {(y == 0).sum():,} ({(y == 0).sum()/len(y)*100:.2f}%)")
    print(f"  Class 1 (Rug-pull): {(y == 1).sum():,} ({(y == 1).sum()/len(y)*100:.2f}%)")
    
    # Check for any remaining NaN values
    nan_count = X.isnull().sum().sum()
    if nan_count > 0:
        print(f"\n⚠ Found {nan_count} NaN values, filling with 0...")
        X = X.fillna(0)
    
    # Apply StandardScaler
    print(f"\n✓ Applying StandardScaler to all {len(feature_cols)} features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Convert back to DataFrame
    X_scaled_df = pd.DataFrame(X_scaled, columns=feature_cols)
    
    # Create final dataset with scaled features + target
    final_df = pd.concat([X_scaled_df, y.reset_index(drop=True)], axis=1)
    
    print(f"   Scaled feature stats (mean should be ~0, std should be ~1):")
    print(f"   - Mean of means: {X_scaled_df.mean().mean():.6f}")
    print(f"   - Mean of stds: {X_scaled_df.std().mean():.6f}")
    
    # Save scaler
    Path('scalers').mkdir(exist_ok=True)
    with open('scalers/solana_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print(f"\n✓ Saved scaler to: scalers/solana_scaler.pkl")
    
    # Save final features
    final_df.to_csv('solana_features.csv', index=False)
    print(f"✓ Saved features to: solana_features.csv")
    print(f"  Shape: {final_df.shape[0]:,} rows × {final_df.shape[1]} columns (features + IS_RUGPULL)")
    
    return final_df, feature_cols


def main():
    """Main feature engineering function"""
    print("Starting feature engineering...\n")
    
    # Engineer features for both datasets
    eth_df, eth_features = engineer_ethereum_features()
    sol_df, sol_features = engineer_solana_features()
    
    # Summary
    print("\n" + "="*80)
    print("FEATURE ENGINEERING COMPLETE - SUMMARY")
    print("="*80)
    
    print("\nEthereum:")
    print(f"  Features: {len(eth_features)} behavioral columns")
    print(f"  Dataset: {eth_df.shape[0]:,} rows × {eth_df.shape[1]} columns")
    print(f"  Scaler: scalers/ethereum_scaler.pkl")
    print(f"  Output: ethereum_features.csv")
    
    print("\nSolana:")
    print(f"  Features: {len(sol_features)} selected columns")
    print(f"    {sol_features}")
    print(f"  Dataset: {sol_df.shape[0]:,} rows × {sol_df.shape[1]} columns")
    print(f"  Scaler: scalers/solana_scaler.pkl")
    print(f"  Output: solana_features.csv")
    
    print("\n✓ Both datasets scaled (mean≈0, std≈1)")
    print("✓ Scalers saved for future predictions")
    print("✓ Ready for Step 5: Train/Validation/Test Split")


if __name__ == "__main__":
    main()
