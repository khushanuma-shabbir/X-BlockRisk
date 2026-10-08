"""
Ultra Simple Blockchain Fraud Detector - Research Prototype
"""

import streamlit as st
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
import pickle
import sys
import os
import numpy as np
from sklearn.neighbors import NearestNeighbors

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.live.fetch_ethereum import fetch_ethereum_wallet
from src.live.fetch_solana import fetch_solana_pool
from src.detection.hybrid_detector import HybridDetector


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
    """Load GNN-22 model (non-ERC20 features only)"""
    base_path = os.path.join(os.path.dirname(__file__), '..')
    
    # Load GNN-22 checkpoint
    checkpoint = torch.load(
        os.path.join(base_path, 'models/ethereum_clean/gnn_22feat.pt'),
        weights_only=False
    )
    
    # Load scaler
    with open(os.path.join(base_path, 'models/ethereum_clean/scaler_22feat.pkl'), 'rb') as f:
        eth_scaler = pickle.load(f)
    
    # Load training features for k-NN
    train_features = np.load(os.path.join(base_path, 'models/ethereum_clean/train_features_22.npy'))
    
    # Initialize model
    eth_model = GraphSAGE(22, 64, 2, 0.4)
    eth_model.load_state_dict(checkpoint['model_state_dict'])
    eth_model.eval()
    
    # Extract metadata
    threshold = checkpoint['threshold']
    feature_list = checkpoint['feature_list']
    
    # Solana (unchanged)
    sol_graph = torch.load(os.path.join(base_path, 'data/processed/solana_graph.pt'), weights_only=False)
    sol_model = GraphSAGE(sol_graph.num_features, 64, 2, 0.4)
    sol_model.load_state_dict(torch.load(os.path.join(base_path, 'models/solana/model_tuned.pt'), weights_only=True))
    sol_model.eval()
    
    with open(os.path.join(base_path, 'models/solana/scaler.pkl'), 'rb') as f:
        sol_scaler = pickle.load(f)
    
    return eth_model, train_features, eth_scaler, threshold, feature_list, sol_model, sol_graph, sol_scaler


def predict_risk(model, train_features, scaler, features, threshold, feature_list, address, is_ethereum=True):
    """
    Predict fraud risk using Hybrid Detection (GNN + Rules + Blacklist + Admin-Control)
    """
    # Step 1: Get GNN prediction
    feature_vector = np.array([features.get(f, 0.0) for f in feature_list])
    feature_vector_log = np.sign(feature_vector) * np.log1p(np.abs(feature_vector))
    features_scaled = scaler.transform(feature_vector_log.reshape(1, -1))[0]
    
    # Find 10 nearest neighbors in training data
    knn = NearestNeighbors(n_neighbors=10, metric='euclidean')
    knn.fit(train_features)
    distances, indices = knn.kneighbors([features_scaled])
    
    # Build mini-graph: new node + 10 neighbors + neighbor connections
    new_node_idx = train_features.shape[0]
    edge_list = []
    
    # Connect new node to 10 neighbors
    for neighbor_idx in indices[0]:
        edge_list.append([new_node_idx, neighbor_idx])
        edge_list.append([neighbor_idx, new_node_idx])
    
    # Connect neighbors to each other
    for i, idx1 in enumerate(indices[0]):
        for idx2 in indices[0][i+1:]:
            edge_list.append([idx1, idx2])
            edge_list.append([idx2, idx1])
    
    # Feature matrix: train + new
    x_all = np.vstack([train_features, features_scaled])
    x_tensor = torch.FloatTensor(x_all)
    edge_index = torch.LongTensor(edge_list).t()
    
    # Run GNN inference
    with torch.no_grad():
        out = model(x_tensor, edge_index)
        probs = torch.exp(out)[new_node_idx]
        fraud_prob = probs[1].item()
    
    gnn_score = fraud_prob * 100
    
    # Step 2: Apply Hybrid Detection
    hybrid_detector = HybridDetector()
    final_score, category, explanations = hybrid_detector.detect(
        address=address,
        features=features,
        gnn_score=gnn_score
    )
    
    risk_score = int(final_score)
    
    # Format explanations for UI
    reasons = []
    for exp in explanations:
        if exp.strip():
            reasons.append(exp)
    
    return risk_score, reasons


# Page config
st.set_page_config(
    page_title="Fraud Detector",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed"
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
st.markdown("<p style='text-align: center; color: gray;'>Hybrid AI - GNN + Rules + Blacklist + Admin-Control Detection</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Load models
eth_model, train_features, eth_scaler, threshold, feature_list, sol_model, sol_graph, sol_scaler = load_models()

# Input
address = st.text_input(
    "Enter wallet address:",
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
                # Ethereum only (GNN-22)
                if address.startswith('0x'):
                    try:
                        features, _, _, data_source = fetch_ethereum_wallet(address)
                    except RuntimeError as e:
                        st.error(f"❌ API Error: {str(e)}")
                        st.stop()
                    
                    if features:
                        risk_score, reasons = predict_risk(
                            eth_model, train_features, eth_scaler, features, 
                            threshold, feature_list, address, is_ethereum=True
                        )
                    else:
                        st.error("❌ Could not fetch data for this address")
                        st.stop()
                else:
                    st.error("❌ Only Ethereum addresses (0x...) are supported")
                    st.stop()
                
                # Show result
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
                
                # Explainable AI
                st.markdown("---")
                st.markdown("### 🧠 Why This Risk Score?")
                st.markdown("**AI detected these patterns:**")
                
                for reason in reasons:
                    st.markdown(f"- {reason}")
                
                # Recommendation
                st.markdown("---")
                if risk_score < 33:
                    st.info("💡 **Recommendation:** This address shows normal activity patterns.")
                elif risk_score < 66:
                    st.warning("💡 **Recommendation:** Exercise caution. Verify before large transactions.")
                else:
                    st.error("💡 **Recommendation:** High risk detected. Avoid interaction.")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>"
    "Research Prototype | Powered by <a href='https://etherscan.io' target='_blank'>Etherscan.io APIs</a>"
    "</p>", 
    unsafe_allow_html=True
)
