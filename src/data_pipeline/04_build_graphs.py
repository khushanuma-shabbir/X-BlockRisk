"""
STEP 4: Graph Construction for GNN Training
Build PyTorch Geometric graph objects for both datasets
"""

import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import sys
import os

# Add config to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def build_ethereum_graph():
    """
    Build Ethereum graph using k-nearest-neighbor (k=10) on scaled features
    
    LIMITATION: This dataset has no real wallet-to-wallet transaction edges.
    We construct a synthetic similarity graph based on behavioral features.
    This is a stated limitation for GNN modeling.
    """
    print("=" * 80)
    print("ETHEREUM GRAPH CONSTRUCTION")
    print("=" * 80)
    
    # Load cleaned data
    df = pd.read_csv('data/processed/ethereum_clean.csv')
    print(f"Loaded data: {df.shape}")
    
    # Separate features and labels
    labels = df['FLAG'].values
    feature_cols = [col for col in df.columns if col != 'FLAG']
    features = df[feature_cols].values
    
    print(f"\nFeatures shape: {features.shape}")
    print(f"Labels shape: {labels.shape}")
    print(f"Label distribution: {np.bincount(labels)}")
    
    # Scale features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Build k-NN graph (k=10)
    # ⚠️ LIMITATION: Synthetic edges based on feature similarity, not real transactions
    print(f"\n🔗 Building k-NN similarity graph (k=10)...")
    k = 10
    knn = NearestNeighbors(n_neighbors=k+1, metric='euclidean')
    knn.fit(features_scaled)
    distances, indices = knn.kneighbors(features_scaled)
    
    # Build edge list (exclude self-loops)
    edge_list = []
    for i in range(len(indices)):
        for j in range(1, k+1):  # Skip first neighbor (itself)
            neighbor = indices[i, j]
            edge_list.append([i, neighbor])
    
    edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
    
    print(f"   Nodes: {len(labels):,}")
    print(f"   Edges: {edge_index.shape[1]:,}")
    print(f"   ⚠️  NOTE: Edges are synthetic (k-NN similarity), not real transactions")
    
    # Create PyTorch Geometric Data object
    data = Data(
        x=torch.tensor(features_scaled, dtype=torch.float),
        edge_index=edge_index,
        y=torch.tensor(labels, dtype=torch.long)
    )
    
    return data, scaler


def build_solana_graph():
    """
    Build Solana graph by connecting pools sharing the same MINT (token) address
    
    This represents real structural relationships: pools for the same token
    are connected, capturing ecosystem-level patterns.
    """
    print("\n\n")
    print("=" * 80)
    print("SOLANA GRAPH CONSTRUCTION")
    print("=" * 80)
    
    # Load labeled data
    df = pd.read_csv('data/processed/solana_labeled.csv')
    print(f"Loaded data: {df.shape}")
    
    # Select feature columns for GNN
    feature_cols = [
        'REMOVE_RATIO',
        'NUM_LIQUIDITY_ADDS',
        'NUM_LIQUIDITY_REMOVES',
        'TOTAL_ADDED_LIQUIDITY',
        'TOTAL_REMOVED_LIQUIDITY',
        'POOL_LIFETIME_HOURS',
        'ADD_TO_REMOVE_RATIO'
    ]
    
    features = df[feature_cols].values
    labels = df['IS_RUGPULL'].values
    
    print(f"\nFeatures shape: {features.shape}")
    print(f"Labels shape: {labels.shape}")
    print(f"Label distribution: {np.bincount(labels)}")
    
    # Scale features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Build edges by connecting pools with same MINT
    print(f"\n🔗 Building MINT-based graph...")
    mint_to_pools = {}
    for idx, mint in enumerate(df['MINT']):
        if pd.notna(mint):
            if mint not in mint_to_pools:
                mint_to_pools[mint] = []
            mint_to_pools[mint].append(idx)
    
    # Create edges within each MINT group
    # For large groups, limit to k=20 nearest neighbors to avoid quadratic blow-up
    edge_list = []
    from tqdm import tqdm
    
    for mint, pool_indices in tqdm(mint_to_pools.items(), desc="Building edges"):
        n_pools = len(pool_indices)
        
        if n_pools <= 20:
            # Small group: fully connect
            for i in range(n_pools):
                for j in range(i+1, n_pools):
                    edge_list.append([pool_indices[i], pool_indices[j]])
                    edge_list.append([pool_indices[j], pool_indices[i]])  # Undirected
        else:
            # Large group: connect to k=20 nearest neighbors based on features
            pool_features = features_scaled[pool_indices]
            knn = NearestNeighbors(n_neighbors=min(21, n_pools), metric='euclidean')
            knn.fit(pool_features)
            _, indices = knn.kneighbors(pool_features)
            
            for i in range(n_pools):
                for j in range(1, min(21, n_pools)):  # Skip self
                    neighbor_idx = pool_indices[indices[i, j]]
                    edge_list.append([pool_indices[i], neighbor_idx])
    
    if not edge_list:
        print("   ⚠️  WARNING: No edges created (no MINT matches)")
        edge_index = torch.empty((2, 0), dtype=torch.long)
    else:
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
    
    print(f"   Nodes: {len(labels):,}")
    print(f"   Edges: {edge_index.shape[1]:,}")
    print(f"   Unique MINTs: {len(mint_to_pools):,}")
    print(f"   ✅ Edges represent real token-sharing relationships")
    
    # Create PyTorch Geometric Data object
    data = Data(
        x=torch.tensor(features_scaled, dtype=torch.float),
        edge_index=edge_index,
        y=torch.tensor(labels, dtype=torch.long)
    )
    
    return data, scaler


def save_graphs(eth_data, eth_scaler, sol_data, sol_scaler):
    """Save graph objects and scalers"""
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('models/ethereum', exist_ok=True)
    os.makedirs('models/solana', exist_ok=True)
    
    # Save graphs
    torch.save(eth_data, 'data/processed/ethereum_graph.pt')
    torch.save(sol_data, 'data/processed/solana_graph.pt')
    
    # Save scalers (needed for inference)
    import pickle
    with open('models/ethereum/scaler.pkl', 'wb') as f:
        pickle.dump(eth_scaler, f)
    with open('models/solana/scaler.pkl', 'wb') as f:
        pickle.dump(sol_scaler, f)
    
    print("\n" + "=" * 80)
    print("✅ Ethereum graph saved: data/processed/ethereum_graph.pt")
    print("✅ Ethereum scaler saved: models/ethereum/scaler.pkl")
    print("✅ Solana graph saved: data/processed/solana_graph.pt")
    print("✅ Solana scaler saved: models/solana/scaler.pkl")
    print("=" * 80)


if __name__ == "__main__":
    # Check if torch_geometric is installed
    try:
        import torch_geometric
        print("✅ PyTorch Geometric detected\n")
    except ImportError:
        print("❌ ERROR: PyTorch Geometric not installed!")
        print("   Install with: pip install torch-geometric")
        sys.exit(1)
    
    eth_data, eth_scaler = build_ethereum_graph()
    sol_data, sol_scaler = build_solana_graph()
    save_graphs(eth_data, eth_scaler, sol_data, sol_scaler)
    
    print("\n✅ STEP 4 COMPLETE - Graph construction finished")
