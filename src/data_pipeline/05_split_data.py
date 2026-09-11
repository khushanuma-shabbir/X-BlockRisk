"""
STEP 5: Train/Validation/Test Split (70/15/15 Stratified)
Split both graphs and save to test_data/ folders
"""

import torch
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os


def split_and_save_graph(graph_path, dataset_name, output_dir):
    """
    Split graph data into train/val/test (70/15/15) stratified by label
    Save as CSV files with node indices for later GNN training
    """
    print("=" * 80)
    print(f"{dataset_name.upper()} - TRAIN/VAL/TEST SPLIT")
    print("=" * 80)
    
    # Load graph (PyTorch 2.6+ requires weights_only=False for custom objects)
    data = torch.load(graph_path, weights_only=False)
    
    features = data.x.numpy()
    labels = data.y.numpy()
    
    print(f"Total samples: {len(labels):,}")
    print(f"Features: {features.shape[1]} dimensions")
    print(f"Label distribution: {np.bincount(labels)}")
    
    # Create indices
    indices = np.arange(len(labels))
    
    # First split: 70% train, 30% temp
    train_idx, temp_idx, y_train, y_temp = train_test_split(
        indices, labels,
        test_size=0.30,
        stratify=labels,
        random_state=42
    )
    
    # Second split: 15% val, 15% test (from the 30% temp)
    val_idx, test_idx, y_val, y_test = train_test_split(
        temp_idx, y_temp,
        test_size=0.50,  # 50% of 30% = 15%
        stratify=y_temp,
        random_state=42
    )
    
    print(f"\n📊 Split sizes:")
    print(f"  Train: {len(train_idx):,} ({len(train_idx)/len(labels)*100:.1f}%)")
    print(f"  Val:   {len(val_idx):,} ({len(val_idx)/len(labels)*100:.1f}%)")
    print(f"  Test:  {len(test_idx):,} ({len(test_idx)/len(labels)*100:.1f}%)")
    
    print(f"\n🎯 Class balance:")
    print(f"  Train: {np.bincount(y_train)}")
    print(f"  Val:   {np.bincount(y_val)}")
    print(f"  Test:  {np.bincount(y_test)}")
    
    # Save to CSV files
    os.makedirs(output_dir, exist_ok=True)
    
    # Save train
    train_df = pd.DataFrame(features[train_idx])
    train_df['label'] = y_train
    train_df['node_idx'] = train_idx
    train_df.to_csv(f'{output_dir}/train.csv', index=False)
    
    # Save val
    val_df = pd.DataFrame(features[val_idx])
    val_df['label'] = y_val
    val_df['node_idx'] = val_idx
    val_df.to_csv(f'{output_dir}/val.csv', index=False)
    
    # Save test
    test_df = pd.DataFrame(features[test_idx])
    test_df['label'] = y_test
    test_df['node_idx'] = test_idx
    test_df.to_csv(f'{output_dir}/test.csv', index=False)
    
    print(f"\n✅ Saved to {output_dir}/")
    
    return {
        'train': (len(train_idx), np.bincount(y_train)),
        'val': (len(val_idx), np.bincount(y_val)),
        'test': (len(test_idx), np.bincount(y_test))
    }


def save_readme(eth_stats, sol_stats):
    """Save README with split statistics"""
    
    # Ethereum README
    eth_readme = f"""ETHEREUM FRAUD DETECTION - DATASET SPLITS
{'=' * 60}

TRAIN SET:
  Rows: {eth_stats['train'][0]:,}
  Class distribution: Legitimate={eth_stats['train'][1][0]:,}, Fraud={eth_stats['train'][1][1]:,}

VALIDATION SET:
  Rows: {eth_stats['val'][0]:,}
  Class distribution: Legitimate={eth_stats['val'][1][0]:,}, Fraud={eth_stats['val'][1][1]:,}

TEST SET:
  Rows: {eth_stats['test'][0]:,}
  Class distribution: Legitimate={eth_stats['test'][1][0]:,}, Fraud={eth_stats['test'][1][1]:,}

SPLIT STRATEGY:
  - 70% Train / 15% Validation / 15% Test
  - Stratified by label to preserve class balance
  - Random seed: 42 (reproducible)

PURPOSE:
  - Train: Model training
  - Val: Hyperparameter tuning and early stopping
  - Test: Final unbiased performance evaluation
"""
    
    with open('data/splits/ethereum/README.txt', 'w') as f:
        f.write(eth_readme)
    
    # Solana README
    sol_readme = f"""SOLANA RUG-PULL DETECTION - DATASET SPLITS
{'=' * 60}

TRAIN SET:
  Rows: {sol_stats['train'][0]:,}
  Class distribution: Legitimate={sol_stats['train'][1][0]:,}, Rug-pull={sol_stats['train'][1][1]:,}

VALIDATION SET:
  Rows: {sol_stats['val'][0]:,}
  Class distribution: Legitimate={sol_stats['val'][1][0]:,}, Rug-pull={sol_stats['val'][1][1]:,}

TEST SET:
  Rows: {sol_stats['test'][0]:,}
  Class distribution: Legitimate={sol_stats['test'][1][0]:,}, Rug-pull={sol_stats['test'][1][1]:,}

SPLIT STRATEGY:
  - 70% Train / 15% Validation / 15% Test
  - Stratified by label to preserve class balance
  - Random seed: 42 (reproducible)

PURPOSE:
  - Train: Model training
  - Val: Hyperparameter tuning and early stopping
  - Test: Final unbiased performance evaluation
"""
    
    with open('data/splits/solana/README.txt', 'w') as f:
        f.write(sol_readme)
    
    print("\n✅ README files saved")


if __name__ == "__main__":
    # Split Ethereum
    eth_stats = split_and_save_graph(
        'data/processed/ethereum_graph.pt',
        'ethereum',
        'data/splits/ethereum'
    )
    
    # Split Solana
    sol_stats = split_and_save_graph(
        'data/processed/solana_graph.pt',
        'solana',
        'data/splits/solana'
    )
    
    # Save READMEs
    save_readme(eth_stats, sol_stats)
    
    print("\n" + "=" * 80)
    print("✅ STEP 5 COMPLETE - Data splitting finished")
    print("=" * 80)
