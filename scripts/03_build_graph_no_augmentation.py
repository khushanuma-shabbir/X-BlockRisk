"""
BUILD GRAPH WITHOUT AUGMENTATION (for comparison)

Same pipeline as 02_augment_and_build_graph.py but skips augmentation step.
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
print("GRAPH CONSTRUCTION (NO AUGMENTATION)")
print("="*80)

# Load splits
print("\n[1/4] Loading train/test splits...")
train_df = pd.read_csv('data/splits/ethereum/train.csv')
test_df = pd.read_csv('data/splits/ethereum/test.csv')

feature_cols = [col for col in train_df.columns if col not in ['Address', 'FLAG']]

X_train = train_df[feature_cols].values
y_train = train_df['FLAG'].values
X_test = test_df[feature_cols].values
y_test = test_df['FLAG'].values

print(f"  Train: {len(X_train):,} (NO augmentation)")
print(f"  Test: {len(X_test):,}")

# Fit scaler on train only
print("\n[2/4] Fitting scaler on train...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

X_all = np.vstack([X_train_scaled, X_test_scaled])
y_all = np.concatenate([y_train, y_test])

# Build graph
print("\n[3/4] Building k-NN graph...")
k = 10
adj_matrix = kneighbors_graph(X_all, n_neighbors=k, mode='connectivity', include_self=False, n_jobs=-1)
edge_index = torch.LongTensor(np.array(adj_matrix.nonzero()))

print(f"  Edges: {edge_index.shape[1]:,}")

# Save
print("\n[4/4] Saving...")
x = torch.FloatTensor(X_all)
y = torch.LongTensor(y_all)
data = Data(x=x, edge_index=edge_index, y=y)

train_mask = torch.zeros(len(X_all), dtype=torch.bool)
test_mask = torch.zeros(len(X_all), dtype=torch.bool)
train_mask[:len(X_train)] = True
test_mask[len(X_train):] = True

data.train_mask = train_mask
data.test_mask = test_mask

torch.save(data, 'data/processed/ethereum_graph_no_aug.pt')
with open('models/ethereum/scaler_no_aug.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("  ✓ Saved graph: data/processed/ethereum_graph_no_aug.pt")
print("  ✓ Saved scaler: models/ethereum/scaler_no_aug.pkl")
print("\n✓ Done")
