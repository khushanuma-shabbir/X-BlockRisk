"""
Comprehensive Fraud Detection Pipeline Debugger
Tests the entire pipeline with known addresses to identify root cause of high scores
"""

import sys
import os

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
import pickle
from sklearn.neighbors import NearestNeighbors

from src.live.fetch_ethereum import fetch_ethereum_wallet
from src.live.fetch_solana import fetch_solana_pool


class GraphSAGE(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels, dropout=0.4):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)
        self.conv3 = SAGEConv(hidden_channels, out_channels)
        self.dropout = dropout
    
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv3(x, edge_index)
        return F.log_softmax(x, dim=1)


def load_models():
    """Load trained models and scalers"""
    print("\n" + "="*80)
    print("LOADING MODELS AND SCALERS")
    print("="*80)
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Ethereum
    eth_graph_path = os.path.join(base_path, 'data/processed/ethereum_graph_augmented.pt')
    eth_model_path = os.path.join(base_path, 'models/ethereum/model_augmented.pt')
    eth_scaler_path = os.path.join(base_path, 'models/ethereum/scaler_augmented.pkl')
    
    print(f"\nLoading Ethereum model:")
    print(f"  Graph: {eth_graph_path}")
    print(f"  Model: {eth_model_path}")
    print(f"  Scaler: {eth_scaler_path}")
    
    eth_graph = torch.load(eth_graph_path, weights_only=False)
    eth_model = GraphSAGE(eth_graph.num_features, 64, 2, 0.4)
    eth_model.load_state_dict(torch.load(eth_model_path, weights_only=True))
    eth_model.eval()
    
    with open(eth_scaler_path, 'rb') as f:
        eth_scaler = pickle.load(f)
    
    print(f"  ✅ Loaded: {eth_graph.num_nodes} nodes, {eth_graph.num_features} features")
    
    # Solana
    sol_graph_path = os.path.join(base_path, 'data/processed/solana_graph.pt')
    sol_model_path = os.path.join(base_path, 'models/solana/model_tuned.pt')
    sol_scaler_path = os.path.join(base_path, 'models/solana/scaler.pkl')
    
    print(f"\nLoading Solana model:")
    print(f"  Graph: {sol_graph_path}")
    print(f"  Model: {sol_model_path}")
    print(f"  Scaler: {sol_scaler_path}")
    
    sol_graph = torch.load(sol_graph_path, weights_only=False)
    sol_model = GraphSAGE(sol_graph.num_features, 64, 2, 0.4)
    sol_model.load_state_dict(torch.load(sol_model_path, weights_only=True))
    sol_model.eval()
    
    with open(sol_scaler_path, 'rb') as f:
        sol_scaler = pickle.load(f)
    
    print(f"  ✅ Loaded: {sol_graph.num_nodes} nodes, {sol_graph.num_features} features")
    print("="*80)
    
    return eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler


def predict_risk_debug(model, graph, scaler, features, is_ethereum=True):
    """
    Predict fraud risk with comprehensive debugging output
    """
    print("\n" + "="*80)
    print("STEP 2: FEATURE VECTOR BEFORE SCALING")
    print("="*80)
    print(f"Raw features (count={len(features)}):")
    for i, (k, v) in enumerate(features.items()):
        print(f"  [{i:2d}] {k:45s} = {v:15.6f}")
    
    # Check for invalid values
    invalid_features = [(k, v) for k, v in features.items() if not isinstance(v, (int, float)) or (isinstance(v, float) and (v != v or abs(v) == float('inf')))]
    if invalid_features:
        print(f"\n⚠️  WARNING: Found {len(invalid_features)} invalid features:")
        for k, v in invalid_features:
            print(f"  - {k} = {v}")
    
    print("\n" + "="*80)
    print("STEP 3: SCALING/NORMALIZATION")
    print("="*80)
    print(f"Scaler type: {type(scaler).__name__}")
    
    if hasattr(scaler, 'mean_'):
        print(f"Scaler mean (first 10): {scaler.mean_[:10]}")
        print(f"Scaler scale (first 10): {scaler.scale_[:10]}")
    else:
        print("Scaler does not have mean_/scale_ attributes")
    
    features_scaled = scaler.transform([list(features.values())])[0]
    
    print(f"\nScaled features (count={len(features_scaled)}):")
    for i, val in enumerate(features_scaled):
        print(f"  [{i:2d}] {val:15.6f}")
    
    # Check for extreme scaled values
    extreme_vals = [(i, val) for i, val in enumerate(features_scaled) if abs(val) > 10]
    if extreme_vals:
        print(f"\n⚠️  WARNING: Found {len(extreme_vals)} extreme scaled values (|z| > 10):")
        for i, val in extreme_vals:
            feature_name = list(features.keys())[i] if i < len(features) else f"feature_{i}"
            print(f"  - Feature {i} ({feature_name}): {val:.2f}")
    
    print("\n" + "="*80)
    print("STEP 4: GRAPH CONSTRUCTION (GNN)")
    print("="*80)
    print(f"Training graph nodes: {graph.num_nodes}")
    print(f"Training graph edges: {graph.edge_index.shape[1]}")
    print(f"Training graph features per node: {graph.num_features}")
    
    knn = NearestNeighbors(n_neighbors=10, metric='euclidean')
    knn.fit(graph.x.numpy())
    distances, indices = knn.kneighbors([features_scaled])
    
    print(f"\nFinding 10 nearest neighbors for new node...")
    print(f"Neighbor indices: {indices[0]}")
    print(f"Neighbor distances: {distances[0]}")
    print(f"Mean neighbor distance: {distances[0].mean():.4f}")
    print(f"Min neighbor distance: {distances[0].min():.4f}")
    print(f"Max neighbor distance: {distances[0].max():.4f}")
    
    new_node_idx = graph.num_nodes
    new_edges = [[new_node_idx, idx] for idx in indices[0]] + [[idx, new_node_idx] for idx in indices[0]]
    
    print(f"\nCreated new node at index: {new_node_idx}")
    print(f"Added {len(new_edges)} edges (bidirectional connections to {len(indices[0])} neighbors)")
    
    new_x = torch.cat([graph.x, torch.FloatTensor([features_scaled])], dim=0)
    new_edge_index = torch.cat([graph.edge_index, torch.LongTensor(new_edges).t()], dim=1)
    
    print(f"New graph nodes: {new_x.shape[0]}")
    print(f"New graph edges: {new_edge_index.shape[1]}")
    
    print("\n" + "="*80)
    print("STEP 5: RAW MODEL OUTPUT")
    print("="*80)
    
    with torch.no_grad():
        out = model(new_x, new_edge_index)
        raw_logits = out[new_node_idx]
        raw_probs = torch.exp(raw_logits)
        fraud_prob = raw_probs[1].item()
        benign_prob = raw_probs[0].item()
    
    print(f"Raw logits: {raw_logits.numpy()}")
    print(f"Raw probabilities (after exp):")
    print(f"  - Class 0 (benign): {benign_prob:.6f}")
    print(f"  - Class 1 (fraud):  {fraud_prob:.6f}")
    print(f"  - Sum (should be ~1.0): {benign_prob + fraud_prob:.6f}")
    
    risk_score = int(fraud_prob * 100)
    
    print(f"\nFinal risk score: {risk_score}/100")
    print("="*80 + "\n")
    
    return risk_score


def test_address(address, eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler, label=""):
    """Test a single address through the entire pipeline"""
    print("\n\n" + "█"*80)
    print(f"TESTING ADDRESS: {address}")
    if label:
        print(f"LABEL: {label}")
    print("█"*80)
    
    try:
        if address.startswith('0x'):
            # Ethereum
            features, _, _, data_source = fetch_ethereum_wallet(address)
            if features:
                risk_score = predict_risk_debug(eth_model, eth_graph, eth_scaler, features, is_ethereum=True)
            else:
                print("❌ Failed to fetch features")
                return None
        else:
            # Solana
            features, _, data_source = fetch_solana_pool(address)
            if features:
                risk_score = predict_risk_debug(sol_model, sol_graph, sol_scaler, features, is_ethereum=False)
            else:
                print("❌ Failed to fetch features")
                return None
        
        return risk_score
    
    except Exception as e:
        print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test runner"""
    print("="*80)
    print("FRAUD DETECTION PIPELINE COMPREHENSIVE DEBUGGER")
    print("="*80)
    
    # Load models
    eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler = load_models()
    
    # Test addresses - TO BE PROVIDED BY USER
    print("\n\n" + "="*80)
    print("STEP 6: VALIDATION TEST SET")
    print("="*80)
    print("\nPlease provide test addresses:")
    print("  - 3 known fraud/scam addresses")
    print("  - 3 known legitimate addresses")
    print("\nYou can modify this script or run interactively.")
    print("="*80)
    
    # Example test addresses (user should replace these)
    test_cases = [
        # FRAUD ADDRESSES - Replace with real known fraud addresses
        # ("0xFRAUD_ADDRESS_1", "Known Scam #1"),
        # ("0xFRAUD_ADDRESS_2", "Known Scam #2"),
        # ("0xFRAUD_ADDRESS_3", "Known Scam #3"),
        
        # LEGITIMATE ADDRESSES - Replace with real known legitimate addresses
        # ("0xLEGIT_ADDRESS_1", "Legitimate Wallet #1"),
        # ("0xLEGIT_ADDRESS_2", "Legitimate Wallet #2"),
        # ("0xLEGIT_ADDRESS_3", "Legitimate Wallet #3"),
        
        # Example: Vitalik's address (known legitimate)
        ("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "Vitalik Buterin (Legitimate)"),
    ]
    
    results = []
    
    for address, label in test_cases:
        risk_score = test_address(address, eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler, label)
        if risk_score is not None:
            results.append((label, address, risk_score))
    
    # Summary
    print("\n\n" + "="*80)
    print("FINAL VALIDATION SUMMARY")
    print("="*80)
    
    if results:
        print(f"\n{'Label':<40} {'Address':<45} {'Risk Score':>10}")
        print("-"*100)
        for label, address, score in results:
            print(f"{label:<40} {address:<45} {score:>10}/100")
        
        print("\n" + "="*80)
        print("EXPECTED BEHAVIOR:")
        print("  - Fraud addresses should score > 66 (high risk)")
        print("  - Legitimate addresses should score < 33 (low risk)")
        print("="*80)
    else:
        print("No results to display. Please add test addresses.")


if __name__ == "__main__":
    main()
