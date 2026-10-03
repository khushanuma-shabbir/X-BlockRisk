"""
AUGMENTATION AND GRAPH CONSTRUCTION

Pipeline:
1. Load train/test splits
2. Augment TRAIN data only (scale fraud patterns 5x, 10x, 20x)
3. Fit StandardScaler on TRAIN only
4. Scale train and test separately
5. Build k-NN similarity graph
6. Save graph data and scaler

Author: Capstone Project
Date: 2026-10-04
"""

import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import kneighbors_graph
import pickle
import os

print("="*80)
print("AUGMENTATION AND GRAPH CONSTRUCTION")
print("="*80)

# Step 1: Load splits
print("\n[1/6] Loading train/test splits...")
train_df = pd.read_csv('data/splits/ethereum/train.csv')
test_df = pd.read_csv('data/splits/ethereum/test.csv')

print(f"  Train: {len(train_df):,} rows")
print(f"  Test:  {len(test_df):,} rows")

# Feature columns (exclude Address and FLAG)
feature_cols = [col for col in train_df.columns if col not in ['Address', 'FLAG']]
print(f"  Features: {len(feature_cols)}")

# Step 2: Augment TRAIN data only
print("\n[2/6] Augmenting TRAIN data (fraud patterns only)...")
train_fraud = train_df[train_df['FLAG'] == 1].copy()
train_legit = train_df[train_df['FLAG'] == 0].copy()

print(f"  Original train fraud: {len(train_fraud):,}")
print(f"  Original train legit: {len(train_legit):,}")

# Scaling factors for fraud patterns
scaling_factors = [5, 10, 20]
augmented_fraud_list = [train_fraud]  # Start with original

for scale in scaling_factors:
    scaled = train_fraud.copy()
    
    # Scale transaction counts
    scaled['Sent tnx'] = (scaled['Sent tnx'] * scale).clip(upper=10000)
    scaled['Received Tnx'] = (scaled['Received Tnx'] * scale).clip(upper=10000)
    
    # Scale ETH amounts
    scaled['total Ether sent'] = (scaled['total Ether sent'] * scale).clip(upper=1000000)
    scaled['total ether received'] = (scaled['total ether received'] * scale).clip(upper=1000000)
    
    # Scale unique addresses (sqrt scaling - less aggressive)
    scaled['Unique Sent To Addresses'] = (scaled['Unique Sent To Addresses'] * np.sqrt(scale)).clip(upper=1000)
    scaled['Unique Received From Addresses'] = (scaled['Unique Received From Addresses'] * np.sqrt(scale)).clip(upper=1000)
    
    # Update derived features
    scaled['avg val sent'] = np.where(
        scaled['Sent tnx'] > 0,
        scaled['total Ether sent'] / scaled['Sent tnx'],
        0
    )
    scaled['avg val received'] = np.where(
        scaled['Received Tnx'] > 0,
        scaled['total ether received'] / scaled['Received Tnx'],
        0
    )
    
    # Recalculate balance
    scaled['total ether balance'] = scaled['total ether received'] - scaled['total Ether sent']
    
    # Scale time span (sqrt)
    scaled['Time Diff between first and last (Mins)'] = (
        scaled['Time Diff between first and last (Mins)'] * np.sqrt(scale)
    ).clip(upper=1000000)
    
    # Clear Address (augmented samples don't have real addresses)
    scaled['Address'] = 'AUGMENTED_' + scaled['Address'].astype(str) + f'_x{scale}'
    
    augmented_fraud_list.append(scaled)
    print(f"  Created {len(scaled):,} fraud samples at scale x{scale}")

# Combine all fraud (original + augmented)
all_train_fraud = pd.concat(augmented_fraud_list, ignore_index=True)

# Combine fraud + legit for final train set
train_augmented = pd.concat([all_train_fraud, train_legit], ignore_index=True)
train_augmented = train_augmented.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\n  Final augmented train: {len(train_augmented):,} rows")
print(f"    Fraud (inc. augmented): {len(all_train_fraud):,}")
print(f"    Legit (original): {len(train_legit):,}")

# Step 3: Fit scaler on TRAIN only
print("\n[3/6] Fitting StandardScaler on TRAIN data only...")
X_train = train_augmented[feature_cols].values
y_train = train_augmented['FLAG'].values

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

print(f"  Scaler fitted on {len(X_train):,} train samples")
print(f"  Mean of feature means: {scaler.mean_.mean():.6f}")
print(f"  Mean of feature stds: {scaler.scale_.mean():.6f}")

# Step 4: Scale test data using TRAIN scaler
print("\n[4/6] Scaling test data...")
X_test = test_df[feature_cols].values
y_test = test_df['FLAG'].values

X_test_scaled = scaler.transform(X_test)
print(f"  Scaled {len(X_test):,} test samples using train scaler")

# Combine for graph construction
X_all = np.vstack([X_train_scaled, X_test_scaled])
y_all = np.concatenate([y_train, y_test])

print(f"\n  Total nodes in graph: {len(X_all):,}")
print(f"    Train nodes: 0 to {len(X_train_scaled)-1}")
print(f"    Test nodes: {len(X_train_scaled)} to {len(X_all)-1}")

# Step 5: Build k-NN similarity graph
print("\n[5/6] Building k-NN similarity graph...")
k = 10
print(f"  Building {k}-nearest neighbor graph (Euclidean distance)...")

adj_matrix = kneighbors_graph(
    X_all,
    n_neighbors=k,
    mode='connectivity',
    include_self=False,
    n_jobs=-1
)

edge_index = torch.LongTensor(np.array(adj_matrix.nonzero()))

print(f"  Total edges: {edge_index.shape[1]:,}")
print(f"  Average degree: {edge_index.shape[1] / len(X_all):.2f}")

# Check train-test connectivity
train_indices = set(range(len(X_train_scaled)))
test_indices = set(range(len(X_train_scaled), len(X_all)))

edges_from_test_to_train = 0
edges_within_test = 0
for i in range(edge_index.shape[1]):
    src, dst = edge_index[0, i].item(), edge_index[1, i].item()
    if src in test_indices:
        if dst in train_indices:
            edges_from_test_to_train += 1
        elif dst in test_indices:
            edges_within_test += 1

test_edges_total = sum(1 for i in range(edge_index.shape[1]) if edge_index[0, i].item() in test_indices)

print(f"\n  Graph structure analysis:")
print(f"    Test node edges: {test_edges_total:,}")
print(f"    Test->Train edges: {edges_from_test_to_train:,} ({edges_from_test_to_train/test_edges_total*100:.1f}%)")
print(f"    Test->Test edges: {edges_within_test:,} ({edges_within_test/test_edges_total*100:.1f}%)")
print(f"  ⚠️  This is a SIMILARITY GRAPH (k-NN), not a transaction graph")

# Step 6: Save
print("\n[6/6] Saving graph data and scaler...")

# Create PyTorch Geometric Data object
x = torch.FloatTensor(X_all)
y = torch.LongTensor(y_all)
data = Data(x=x, edge_index=edge_index, y=y)

# Create train/test masks
train_mask = torch.zeros(len(X_all), dtype=torch.bool)
test_mask = torch.zeros(len(X_all), dtype=torch.bool)
train_mask[:len(X_train_scaled)] = True
test_mask[len(X_train_scaled):] = True

data.train_mask = train_mask
data.test_mask = test_mask

# Save
os.makedirs('data/processed', exist_ok=True)
os.makedirs('models/ethereum', exist_ok=True)

graph_path = 'data/processed/ethereum_graph_clean.pt'
scaler_path = 'models/ethereum/scaler_clean.pkl'

torch.save(data, graph_path)
print(f"  ✓ Saved graph: {graph_path}")

with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"  ✓ Saved scaler: {scaler_path}")

# Also save augmented train data for reference
train_augmented.to_csv('data/processed/ethereum_train_augmented.csv', index=False)
print(f"  ✓ Saved augmented train: data/processed/ethereum_train_augmented.csv")

# Summary
print("\n" + "="*80)
print("AUGMENTATION AND GRAPH CONSTRUCTION COMPLETE")
print("="*80)
print(f"\nGraph type: k-NN Similarity Graph (k={k})")
print(f"  - Edges connect nodes with similar feature vectors")
print(f"  - Test nodes CAN connect to train nodes (information leakage concern)")
print(f"  - GNN aggregates features from neighbors during message passing")

print(f"\nDataset:")
print(f"  Train nodes: {train_mask.sum():,} (includes augmented fraud)")
print(f"  Test nodes: {test_mask.sum():,} (original data only)")
print(f"  Features per node: {x.shape[1]}")
print(f"  Edges: {edge_index.shape[1]:,}")

print(f"\n✓ Ready for model training")
