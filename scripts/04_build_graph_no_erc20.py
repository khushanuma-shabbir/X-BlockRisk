"""
BUILD GRAPH WITH ERC20 COLUMNS REMOVED (22 features)
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
print("GRAPH CONSTRUCTION (NO ERC20 FEATURES)")
print("="*80)

train_df = pd.read_csv('data/splits/ethereum/train.csv')
test_df = pd.read_csv('data/splits/ethereum/test.csv')

# Select only non-ERC20 features
all_features = [col for col in train_df.columns if col not in ['Address', 'FLAG']]
non_erc20_features = [col for col in all_features if 'ERC20' not in col and 'ERC 20' not in col]

print(f"\n[1/4] Feature selection...")
print(f"  All features: {len(all_features)}")
print(f"  Non-ERC20 features: {len(non_erc20_features)}")
print(f"  Removed: {len(all_features) - len(non_erc20_features)} ERC20 columns")

X_train = train_df[non_erc20_features].values
y_train = train_df['FLAG'].values
X_test = test_df[non_erc20_features].values
y_test = test_df['FLAG'].values

print(f"\n[2/4] Scaling...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

X_all = np.vstack([X_train_scaled, X_test_scaled])
y_all = np.concatenate([y_train, y_test])

print(f"\n[3/4] Building k-NN graph...")
k = 10
adj_matrix = kneighbors_graph(X_all, n_neighbors=k, mode='connectivity', include_self=False, n_jobs=-1)
edge_index = torch.LongTensor(np.array(adj_matrix.nonzero()))

print(f"  Edges: {edge_index.shape[1]:,}")

print(f"\n[4/4] Saving...")
x = torch.FloatTensor(X_all)
y = torch.LongTensor(y_all)
data = Data(x=x, edge_index=edge_index, y=y)

train_mask = torch.zeros(len(X_all), dtype=torch.bool)
test_mask = torch.zeros(len(X_all), dtype=torch.bool)
train_mask[:len(X_train)] = True
test_mask[len(X_train):] = True

data.train_mask = train_mask
data.test_mask = test_mask

torch.save(data, 'data/processed/ethereum_graph_no_erc20.pt')
with open('models/ethereum/scaler_no_erc20.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("  ✓ Saved graph: data/processed/ethereum_graph_no_erc20.pt")
print("  ✓ Saved scaler: models/ethereum/scaler_no_erc20.pkl")
print("\n✓ Done")
