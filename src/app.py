"""
Ultra Simple Blockchain Fraud Detector
"""

import streamlit as st
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
import pickle
import sys
import os
from sklearn.neighbors import NearestNeighbors

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

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


@st.cache_resource
def load_models():
    base_path = os.path.join(os.path.dirname(__file__), '..')
    
    eth_graph = torch.load(os.path.join(base_path, 'data/processed/ethereum_graph_augmented.pt'), weights_only=False)
    eth_model = GraphSAGE(eth_graph.num_features, 64, 2, 0.4)
    eth_model.load_state_dict(torch.load(os.path.join(base_path, 'models/ethereum/model_augmented.pt'), weights_only=True))
    eth_model.eval()
    
    with open(os.path.join(base_path, 'models/ethereum/scaler_augmented.pkl'), 'rb') as f:
        eth_scaler = pickle.load(f)
    
    sol_graph = torch.load(os.path.join(base_path, 'data/processed/solana_graph.pt'), weights_only=False)
    sol_model = GraphSAGE(sol_graph.num_features, 64, 2, 0.4)
    sol_model.load_state_dict(torch.load(os.path.join(base_path, 'models/solana/model_tuned.pt'), weights_only=True))
    sol_model.eval()
    
    with open(os.path.join(base_path, 'models/solana/scaler.pkl'), 'rb') as f:
        sol_scaler = pickle.load(f)
    
    return eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler


def predict_risk(model, graph, scaler, features, is_ethereum=True):
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
    print(f"Scaler mean (first 5): {scaler.mean_[:5] if hasattr(scaler, 'mean_') else 'N/A'}")
    print(f"Scaler scale (first 5): {scaler.scale_[:5] if hasattr(scaler, 'scale_') else 'N/A'}")
    
    features_scaled = scaler.transform([list(features.values())])[0]
    
    print(f"\nScaled features (count={len(features_scaled)}):")
    for i, val in enumerate(features_scaled):
        print(f"  [{i:2d}] {val:15.6f}")
    
    # Check for extreme scaled values
    extreme_vals = [(i, val) for i, val in enumerate(features_scaled) if abs(val) > 10]
    if extreme_vals:
        print(f"\n⚠️  WARNING: Found {len(extreme_vals)} extreme scaled values (|z| > 10):")
        for i, val in extreme_vals:
            print(f"  - Feature {i}: {val:.2f}")
    
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
    
    # Generate Explainable AI reasoning
    reasons = []
    
    if is_ethereum:
        sent = features.get('Sent tnx', 0)
        received = features.get('Received Tnx', 0)
        unique_sent = features.get('Unique Sent To Addresses', 0)
        total_eth = features.get('total Ether sent', 0) + features.get('total ether received', 0)
        
        # Reason 1: Activity pattern
        if sent > 100:
            reasons.append(f"📊 High activity: {int(sent)} outgoing transactions")
        elif sent < 10:
            reasons.append(f"📊 Low activity: Only {int(sent)} transactions")
        else:
            reasons.append(f"📊 Moderate activity: {int(sent)} sent, {int(received)} received")
        
        # Reason 2: Distribution pattern
        if unique_sent > 50:
            reasons.append(f"🔗 Interacts with {int(unique_sent)} different addresses (distribution pattern)")
        elif unique_sent > 20:
            reasons.append(f"🔗 Connected to {int(unique_sent)} addresses")
        
        # Reason 3: Volume
        if total_eth > 1000:
            reasons.append(f"💰 High volume: {int(total_eth)} ETH total")
        elif total_eth < 1:
            reasons.append(f"💰 Low volume: {total_eth:.2f} ETH total")
        
    else:  # Solana
        remove_ratio = features.get('REMOVE_RATIO', 0)
        num_adds = features.get('NUM_LIQUIDITY_ADDS', 0)
        lifetime = features.get('POOL_LIFETIME_HOURS', 0)
        
        # Reason 1: Liquidity removal
        if remove_ratio > 0.8:
            reasons.append(f"🚨 {int(remove_ratio*100)}% liquidity removed (major red flag)")
        elif remove_ratio > 0.5:
            reasons.append(f"⚠️ {int(remove_ratio*100)}% liquidity removed")
        else:
            reasons.append(f"✓ Only {int(remove_ratio*100)}% liquidity removed (normal)")
        
        # Reason 2: Community trust
        if num_adds < 5:
            reasons.append(f"👥 Very few participants ({int(num_adds)} liquidity adds)")
        
        # Reason 3: Pool age
        if lifetime < 24:
            reasons.append(f"🕐 Very new pool ({lifetime:.1f} hours old)")
        elif lifetime > 720:
            reasons.append(f"🕐 Established pool ({int(lifetime/24)} days old)")
    
    return risk_score, reasons


# Page config
st.set_page_config(
    page_title="Fraud Detector",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed"  # Hide sidebar
)

# Hide streamlit elements
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align: center;'>🔍 Fraud Detector</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Check if a blockchain address is suspicious</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Load models
eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler = load_models()

# Input
address = st.text_input(
    "Enter wallet or pool address:",
    placeholder="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    label_visibility="collapsed"
)

# Analyze button
if st.button("🚀 Check Address", type="primary", use_container_width=True):
    if not address:
        st.warning("⚠️ Please enter an address")
    else:
        with st.spinner("Analyzing..."):
            try:
                # Detect blockchain and fetch data
                if address.startswith('0x'):
                    features, _, _, data_source = fetch_ethereum_wallet(address)
                    if features:
                        risk_score, reasons = predict_risk(eth_model, eth_graph, eth_scaler, features, is_ethereum=True)
                    else:
                        st.error("❌ Could not fetch data for this address")
                        st.stop()
                else:
                    features, _, data_source = fetch_solana_pool(address)
                    if features:
                        risk_score, reasons = predict_risk(sol_model, sol_graph, sol_scaler, features, is_ethereum=False)
                    else:
                        st.error("❌ Could not fetch data for this address")
                        st.stop()
                
                # Show result with Explainable AI
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Risk score display
                if risk_score < 33:
                    st.success(f"### ✅ Low Risk")
                    st.metric("Risk Score", f"{risk_score}/100", delta="Safe", delta_color="normal")
                elif risk_score < 66:
                    st.warning(f"### ⚠️ Medium Risk")
                    st.metric("Risk Score", f"{risk_score}/100", delta="Caution", delta_color="inverse")
                else:
                    st.error(f"### 🚨 High Risk")
                    st.metric("Risk Score", f"{risk_score}/100", delta="Danger", delta_color="inverse")
                
                # Explainable AI - WHY this risk score?
                st.markdown("---")
                st.markdown("### 🧠 Why This Risk Score?")
                st.markdown("**AI detected these patterns:**")
                
                for reason in reasons:
                    st.markdown(f"- {reason}")
                
                # Simple recommendation
                st.markdown("---")
                if risk_score < 33:
                    st.info("💡 **Recommendation:** This address shows normal activity patterns. Appears safe.")
                elif risk_score < 66:
                    st.warning("💡 **Recommendation:** Exercise caution. Verify before any large transactions.")
                else:
                    st.error("💡 **Recommendation:** High risk detected. Avoid interaction unless you're certain.")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray; font-size: 12px;'>AI-powered fraud detection</p>", unsafe_allow_html=True)
