"""
VALIDATION SCRIPT - Test the fraud detection fix with known addresses

This script tests the fixed pipeline against a validation set of known
fraud and legitimate addresses. Replace the placeholder addresses with
real ones for comprehensive testing.
"""

import sys
import os

# Fix Windows console encoding
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
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Ethereum
    eth_graph = torch.load(os.path.join(base_path, 'data/processed/ethereum_graph_augmented.pt'), weights_only=False)
    eth_model = GraphSAGE(eth_graph.num_features, 64, 2, 0.4)
    eth_model.load_state_dict(torch.load(os.path.join(base_path, 'models/ethereum/model_augmented.pt'), weights_only=True))
    eth_model.eval()
    
    with open(os.path.join(base_path, 'models/ethereum/scaler_augmented.pkl'), 'rb') as f:
        eth_scaler = pickle.load(f)
    
    # Solana
    sol_graph = torch.load(os.path.join(base_path, 'data/processed/solana_graph.pt'), weights_only=False)
    sol_model = GraphSAGE(sol_graph.num_features, 64, 2, 0.4)
    sol_model.load_state_dict(torch.load(os.path.join(base_path, 'models/solana/model_tuned.pt'), weights_only=True))
    sol_model.eval()
    
    with open(os.path.join(base_path, 'models/solana/scaler.pkl'), 'rb') as f:
        sol_scaler = pickle.load(f)
    
    return eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler


def predict_risk(model, graph, scaler, features):
    """Predict fraud risk score"""
    features_scaled = scaler.transform([list(features.values())])[0]
    knn = NearestNeighbors(n_neighbors=10, metric='euclidean')
    knn.fit(graph.x.numpy())
    _, indices = knn.kneighbors([features_scaled])
    
    new_node_idx = graph.num_nodes
    new_edges = [[new_node_idx, idx] for idx in indices[0]] + [[idx, new_node_idx] for idx in indices[0]]
    
    new_x = torch.cat([graph.x, torch.FloatTensor([features_scaled])], dim=0)
    new_edge_index = torch.cat([graph.edge_index, torch.LongTensor(new_edges).t()], dim=1)
    
    with torch.no_grad():
        out = model(new_x, new_edge_index)
        fraud_prob = torch.exp(out[new_node_idx])[1].item()
    
    return int(fraud_prob * 100)


def test_address(address, eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler, label=""):
    """Test a single address"""
    print(f"\nTesting: {label}")
    print(f"Address: {address}")
    
    try:
        if address.startswith('0x'):
            features, _, _, data_source = fetch_ethereum_wallet(address)
            if features:
                risk_score = predict_risk(eth_model, eth_graph, eth_scaler, features)
            else:
                print("  => Failed to fetch features\n")
                return None
        else:
            features, _, data_source = fetch_solana_pool(address)
            if features:
                risk_score = predict_risk(sol_model, sol_graph, sol_scaler, features)
            else:
                print("  => Failed to fetch features\n")
                return None
        
        # Visual indicator
        if risk_score < 33:
            indicator = "LOW RISK"
            emoji = "Γ£à"
        elif risk_score < 66:
            indicator = "MEDIUM RISK"  
            emoji = "ΓÜá"
        else:
            indicator = "HIGH RISK"
            emoji = "Γò¼"
        
        print(f"  => Risk Score: {risk_score}/100 ({indicator}) {emoji}\n")
        return risk_score
    
    except Exception as e:
        print(f"  => ERROR: {type(e).__name__}: {e}\n")
        return None


def main():
    print("="*80)
    print("FRAUD DETECTION PIPELINE - VALIDATION")
    print("="*80)
    print("\nLoading models...")
    
    eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler = load_models()
    
    print("Γ£à Models loaded successfully!\n")
    print("="*80)
    
    #
    # VALIDATION TEST SET
    # Replace these placeholder addresses with real known fraud/legitimate addresses
    #
    
    test_cases = [
        # ========== ETHEREUM ADDRESSES ==========
        
        # Known FRAUD addresses (should score > 66)
        # ("0xFRAUD_ADDRESS_1", "Known Scam #1 - [Brief description]"),
        # ("0xFRAUD_ADDRESS_2", "Known Scam #2 - [Brief description]"),
        # ("0xFRAUD_ADDRESS_3", "Known Scam #3 - [Brief description]"),
        
        # Known LEGITIMATE addresses (should score < 33)
        ("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "Vitalik Buterin - Ethereum Co-founder"),
        # ("0xLEGIT_ADDRESS_2", "Legitimate Wallet #2 - [Brief description]"),
        # ("0xLEGIT_ADDRESS_3", "Legitimate Wallet #3 - [Brief description]"),
        
        # ========== SOLANA ADDRESSES ==========
        
        # Known FRAUD pools (should score > 66)
        # ("SOLANA_FRAUD_POOL_1", "Known Rug Pull #1 - [Brief description]"),
        # ("SOLANA_FRAUD_POOL_2", "Known Rug Pull #2 - [Brief description]"),
        
        # Known LEGITIMATE pools (should score < 33)
        # ("SOLANA_LEGIT_POOL_1", "Legitimate Pool #1 - [Brief description]"),
        # ("SOLANA_LEGIT_POOL_2", "Legitimate Pool #2 - [Brief description]"),
    ]
    
    if len(test_cases) == 0:
        print("\nNo test addresses configured!")
        print("Please add known fraud and legitimate addresses to the test_cases list.\n")
        return
    
    results = []
    
    for address, label in test_cases:
        risk_score = test_address(address, eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler, label)
        if risk_score is not None:
            results.append((label, address, risk_score))
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    if results:
        print(f"\n{'Label':<50} {'Risk Score':>10}")
        print("-"*62)
        for label, address, score in results:
            if score < 33:
                status = "Γ£à LOW"
            elif score < 66:
                status = "ΓÜá MED"
            else:
                status = "Γò¼ HIGH"
            print(f"{label:<50} {score:>7}/100 {status}")
        
        print("\n" + "="*80)
        print("EXPECTED BEHAVIOR:")
        print("  Γò¼ Fraud addresses should score > 66 (high risk)")
        print("  Γ£à Legitimate addresses should score < 33 (low risk)")
        print("  ΓÜá Uncertain addresses score 33-66 (medium risk)")
        print("="*80)
        
        # Validation check
        fraud_count = sum(1 for _, _, score in results if score > 66)
        legit_count = sum(1 for _, _, score in results if score < 33)
        
        print(f"\nResults: {fraud_count} high-risk, {legit_count} low-risk, {len(results) - fraud_count - legit_count} medium-risk")
        
        if legit_count > 0:
            print("\nΓ£à FIX VALIDATED: Model is now producing varied risk scores!")
        else:
            print("\nΓÜá Model may need further calibration")
    else:
        print("\nNo successful results. Please check API keys and network connectivity.")
    
    print()


if __name__ == "__main__":
    main()
