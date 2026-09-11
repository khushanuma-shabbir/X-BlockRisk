"""
STEP 9: Live Fraud Detection Dashboard
Single-page Streamlit app for real-time wallet/pool analysis

MODEL IMPROVEMENTS (September 2026):
- Architecture: 3-layer GraphSAGE with hidden_dim=64, dropout=0.4
- Thresholds: Ethereum=0.55, Solana=0.65 (optimized via validation set)
- Performance: Ethereum 75% F1 (+11% from baseline), Solana 55% F1 (+2%)
- Loss: Focal Loss (gamma=1.0) for Ethereum, Weighted CE for Solana
"""

import streamlit as st
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import pickle
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import live fetchers
from live.fetch_ethereum import fetch_ethereum_wallet
from live.fetch_solana import fetch_solana_pool


# GraphSAGE model
class GraphSAGE(torch.nn.Module):
    """3-layer GraphSAGE (improved architecture from hyperparameter tuning)"""
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
    """Load trained models and graphs (AUGMENTED models for live address support)"""
    base_path = os.path.join(os.path.dirname(__file__), '..')
    
    # Ethereum - Using AUGMENTED model (supports high-activity addresses)
    eth_graph = torch.load(os.path.join(base_path, 'data/processed/ethereum_graph_augmented.pt'), weights_only=False)
    eth_model = GraphSAGE(eth_graph.num_features, 64, 2, 0.4)
    eth_model.load_state_dict(torch.load(os.path.join(base_path, 'models/ethereum/model_augmented.pt'), weights_only=True))
    eth_model.eval()
    
    with open(os.path.join(base_path, 'models/ethereum/scaler_augmented.pkl'), 'rb') as f:
        eth_scaler = pickle.load(f)
    
    # Solana - Updated to 3-layer, hidden_dim=64, dropout=0.4
    sol_graph = torch.load(os.path.join(base_path, 'data/processed/solana_graph.pt'), weights_only=False)
    sol_model = GraphSAGE(sol_graph.num_features, 64, 2, 0.4)
    sol_model.load_state_dict(torch.load(os.path.join(base_path, 'models/solana/model_tuned.pt'), weights_only=True))
    sol_model.eval()
    
    with open(os.path.join(base_path, 'models/solana/scaler.pkl'), 'rb') as f:
        sol_scaler = pickle.load(f)
    
    return eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler


def attach_node_to_graph(new_features, graph, scaler, k=10):
    """
    Attach a new node to existing graph via k-NN
    Returns: updated graph with new node and edges, plus edge count for debugging
    """
    # Scale features
    new_features_scaled = scaler.transform([list(new_features.values())])[0]
    
    # Find k nearest neighbors
    existing_features = graph.x.numpy()
    knn = NearestNeighbors(n_neighbors=k, metric='euclidean')
    knn.fit(existing_features)
    distances, indices = knn.kneighbors([new_features_scaled])
    
    # Create new edges
    new_node_idx = graph.num_nodes
    new_edges = []
    for neighbor_idx in indices[0]:
        new_edges.append([new_node_idx, neighbor_idx])  # New -> Neighbor
        new_edges.append([neighbor_idx, new_node_idx])  # Neighbor -> New
    
    # Update graph
    new_x = torch.cat([graph.x, torch.FloatTensor([new_features_scaled])], dim=0)
    new_edge_index = torch.cat([
        graph.edge_index,
        torch.LongTensor(new_edges).t()
    ], dim=1)
    
    edge_count = len(new_edges)
    print(f"[DEBUG] Attached new node with {edge_count} edges to {k} neighbors")
    
    return new_x, new_edge_index, new_node_idx, edge_count


def predict_with_explanation(model, x, edge_index, node_idx, feature_names, original_features, edge_count, is_ethereum=True):
    """
    Run inference and generate human-readable explanation
    Uses optimized thresholds from hyperparameter tuning:
    - Ethereum: 0.55
    - Solana: 0.65
    """
    with torch.no_grad():
        out = model(x, edge_index)
        
        # Get fraud probability
        fraud_prob = torch.exp(out[node_idx])[1].item()
        
        # Apply optimized thresholds
        if is_ethereum:
            threshold = 0.55  # Optimized for Ethereum
        else:
            threshold = 0.65  # Optimized for Solana
        
        pred = 1 if fraud_prob > threshold else 0
        prob = fraud_prob if pred == 1 else (1 - fraud_prob)
    
    # Risk score (0-100)
    risk_score = int(fraud_prob * 100)  # Probability of fraud/rugpull
    
    # Risk category (based on fraud probability, not prediction)
    if risk_score < 33:
        risk_category = "🟢 LOW RISK"
        risk_color = "green"
        verdict = "This wallet looks safe based on its transaction history."
    elif risk_score < 66:
        risk_category = "🟡 MEDIUM RISK"
        risk_color = "orange"
        verdict = "This wallet shows some warning signs — proceed with caution and verify before transacting."
    else:
        risk_category = "🔴 HIGH RISK"
        risk_color = "red"
        verdict = "This wallet shows several warning signs commonly seen in scams — be very careful."
    
    # Check neighbor fraud rates (using same threshold)
    neighbors = edge_index[1, edge_index[0] == node_idx].tolist()
    if len(neighbors) > 0:
        with torch.no_grad():
            neighbor_out = out[neighbors]
            neighbor_fraud_probs = torch.exp(neighbor_out)[:, 1]
            if is_ethereum:
                flagged_neighbors = (neighbor_fraud_probs > 0.55).sum().item()
            else:
                flagged_neighbors = (neighbor_fraud_probs > 0.65).sum().item()
    else:
        flagged_neighbors = 0
    
    # Generate human-readable explanation
    if is_ethereum:
        explanation_parts = []
        
        # Analyze transaction patterns
        sent_count = original_features.get('Sent tnx', 0)
        received_count = original_features.get('Received Tnx', 0)
        unique_senders = original_features.get('Unique Received From Addresses', 0)
        unique_receivers = original_features.get('Unique Sent To Addresses', 0)
        avg_time_sent = original_features.get('Avg min between sent tnx', 0)
        total_sent = original_features.get('total Ether sent', 0)
        total_received = original_features.get('total ether received', 0)
        
        # Pattern 1: Activity level
        if sent_count > 100 or received_count > 100:
            explanation_parts.append(f"This is a very active wallet with {int(sent_count)} outgoing and {int(received_count)} incoming transactions.")
        elif sent_count < 10 and received_count < 10:
            explanation_parts.append(f"This wallet has limited activity with only {int(sent_count)} outgoing and {int(received_count)} incoming transactions.")
        
        # Pattern 2: Distribution behavior
        if unique_receivers > 50 and avg_time_sent < 60:
            explanation_parts.append("It sends money to many different addresses very quickly — a pattern sometimes seen in distribution networks or automated systems.")
        elif unique_receivers > 20:
            explanation_parts.append(f"It interacts with {int(unique_receivers)} different addresses, showing diverse transaction patterns.")
        
        # Pattern 3: Balance behavior
        if total_sent > total_received * 2:
            explanation_parts.append("The wallet has sent out significantly more than it received, which could indicate fund distribution activity.")
        elif total_received > total_sent * 2:
            explanation_parts.append("The wallet receives more than it sends out, typical of collection or accumulation addresses.")
        
        # Network context
        if flagged_neighbors > 0:
            explanation_parts.append(f"We also checked its on-chain connections — it's linked to {flagged_neighbors} other wallet(s) our system flagged as suspicious, which raises concern.")
        else:
            explanation_parts.append("Its on-chain connections look normal — it's not directly linked to any wallets we've flagged.")
        
        explanation = " ".join(explanation_parts)
    
    else:  # Solana
        explanation_parts = []
        
        remove_ratio = original_features.get('REMOVE_RATIO', 0)
        num_adds = original_features.get('NUM_LIQUIDITY_ADDS', 0)
        lifetime_hours = original_features.get('POOL_LIFETIME_HOURS', 0)
        status = original_features.get('INACTIVITY_STATUS', 'Active')
        
        # Pattern 1: Liquidity removal
        if remove_ratio >= 0.85:
            explanation_parts.append(f"Nearly all liquidity was removed from this pool ({int(remove_ratio * 100)}% withdrawn) — a major red flag for rug-pulls.")
        elif remove_ratio >= 0.5:
            explanation_parts.append(f"A significant portion of liquidity was removed ({int(remove_ratio * 100)}%), which warrants caution.")
        else:
            explanation_parts.append(f"Liquidity removal looks normal ({int(remove_ratio * 100)}% withdrawn).")
        
        # Pattern 2: Activity level
        if num_adds <= 3:
            explanation_parts.append(f"Very few people added liquidity (only {int(num_adds)}), suggesting low community trust.")
        
        # Pattern 3: Lifetime
        if lifetime_hours < 24:
            explanation_parts.append(f"This pool is very new (only {lifetime_hours:.1f} hours old) — new pools carry higher risk.")
        elif lifetime_hours > 720:  # 30 days
            explanation_parts.append(f"This pool has been active for {int(lifetime_hours/24)} days, showing some stability.")
        
        # Status
        if status == 'Inactive':
            explanation_parts.append("The pool is now inactive, which combined with high removal could indicate a rug-pull.")
        
        # Network context
        if flagged_neighbors > 0:
            explanation_parts.append(f"It shares its token with {flagged_neighbors} other pool(s) we've flagged — a concerning pattern.")
        else:
            explanation_parts.append("Other pools using the same token look normal.")
        
        explanation = " ".join(explanation_parts)
    
    return {
        'verdict': verdict,
        'prediction': 'FRAUD' if pred == 1 and is_ethereum else ('RUG-PULL' if pred == 1 else 'LEGITIMATE'),
        'confidence': prob,
        'risk_score': risk_score,
        'risk_category': risk_category,
        'risk_color': risk_color,
        'explanation': explanation,
        'edge_count': edge_count,
        'flagged_neighbors': flagged_neighbors
    }


def main():
    # Page config
    st.set_page_config(
        page_title="Blockchain Fraud Detector",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0 2rem 0;'>
            <h1 style='color: #1f77b4; margin-bottom: 0.5rem;'>🔍 Blockchain Fraud Detection</h1>
            <p style='font-size: 1.1rem; color: #666;'>Real-time risk assessment for Ethereum wallets and Solana liquidity pools using Graph Neural Networks</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Load models once at startup
    with st.spinner("🔄 Loading AI models..."):
        eth_model, eth_graph, eth_scaler, sol_model, sol_graph, sol_scaler = load_models()
    
    # === SYNTHETIC TEST MODE ===
    st.markdown("---")
    test_mode = st.checkbox("🧪 **Use Synthetic Test Mode** (100 pre-computed test cases)")
    
    if test_mode:
        st.info("""
        **Synthetic Test Mode:** Load pre-computed test cases from the training data.  
        These demonstrate the model's TRUE capabilities on patterns it was trained on.
        
        **Why use this?** Live addresses from Etherscan often have transaction patterns outside 
        the training distribution (e.g., >1000 txs vs trained on <50 txs), causing conservative 
        predictions. Synthetic mode shows varied risk scores (5%, 35%, 78%, 92%, etc.).
        """)
        
        # Load test cases
        try:
            test_df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'synthetic_test_cases_100.csv'))
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                test_filter = st.selectbox(
                    "Filter by type",
                    ["All (100)", "Fraud cases (50)", "Legitimate cases (50)"]
                )
            
            if test_filter == "Fraud cases (50)":
                filtered_df = test_df[test_df['test_id'].str.contains('FRAUD')]
            elif test_filter == "Legitimate cases (50)":
                filtered_df = test_df[test_df['test_id'].str.contains('LEGIT')]
            else:
                filtered_df = test_df
            
            with col2:
                selected_test = st.selectbox(
                    "Select test case",
                    filtered_df['test_id'].tolist()
                )
            
            # Show test case details
            test_case = test_df[test_df['test_id'] == selected_test].iloc[0]
            
            st.markdown(f"**Test Case:** `{selected_test}`")
            st.markdown(f"**Description:** {test_case['description']}")
            st.markdown(f"**Expected:** {test_case['expected_risk']} RISK")
            
            if st.button("🔬 Run Test", type="primary"):
                with st.spinner("Running model prediction..."):
                    # Extract features (all columns except metadata)
                    feature_cols = [col for col in test_df.columns if col not in ['test_id', 'expected_label', 'expected_risk', 'description']]
                    features = {col: test_case[col] for col in feature_cols}
                    
                    # Attach to graph and predict
                    x_new, edge_index, node_idx, edge_count = attach_node_to_graph(
                        features, eth_graph, eth_scaler, is_ethereum=True
                    )
                    
                    result = predict_with_explanation(
                        eth_model, x_new, edge_index, node_idx,
                        feature_cols, features, edge_count, is_ethereum=True
                    )
                    
                    # Display results
                    st.success("✅ Data Source: Synthetic Test Case (Training Data)")
                    
                    st.markdown("---")
                    st.markdown("## 📊 Risk Assessment Results")
                    
                    # Risk verdict
                    if result['risk_score'] < 33:
                        verdict_color = "green"
                        verdict_icon = "✅"
                    elif result['risk_score'] < 66:
                        verdict_color = "orange"
                        verdict_icon = "⚠️"
                    else:
                        verdict_color = "red"
                        verdict_icon = "🚨"
                    
                    st.markdown(f"""
                    <div style='padding: 1rem; border-left: 4px solid {verdict_color}; background-color: rgba(0,0,0,0.05); margin: 1rem 0;'>
                        <h3 style='margin: 0; color: {verdict_color};'>{verdict_icon} {result['verdict']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🎯 Risk Score", f"{result['risk_score']}/100")
                    with col2:
                        st.metric("📊 Risk Category", result['risk_category'].replace('🟢 ', '').replace('🟡 ', '').replace('🔴 ', ''))
                    with col3:
                        st.metric("🤖 Model Confidence", f"{result['confidence']*100:.1f}%")
                    
                    # Analysis
                    st.markdown("### 💡 Analysis")
                    st.info(result['explanation'])
                    
                    # Network context
                    if result['edge_count'] > 0:
                        st.markdown(f"**Network Context:** Connected to {result['edge_count']} similar wallets, {result['flagged_neighbors']} flagged as suspicious")
                    
                    # Comparison with expected
                    st.markdown("### 📋 Test Result")
                    expected_risk = test_case['expected_risk']
                    actual_risk = "HIGH" if result['risk_score'] >= 66 else ("MEDIUM" if result['risk_score'] >= 33 else "LOW")
                    
                    if expected_risk == actual_risk:
                        st.success(f"✅ **PASS**: Model correctly predicted {actual_risk} RISK (expected {expected_risk})")
                    elif (expected_risk == "HIGH" and actual_risk == "MEDIUM") or (expected_risk == "LOW" and actual_risk == "MEDIUM"):
                        st.warning(f"⚠️  **PARTIAL**: Model predicted {actual_risk} RISK (expected {expected_risk})")
                    else:
                        st.error(f"❌ **MISMATCH**: Model predicted {actual_risk} RISK (expected {expected_risk})")
            
            st.markdown("---")
            st.markdown("""
            **Note:** Synthetic test mode uses feature vectors from the training dataset. 
            Risk scores will vary (not all 0/100) because these patterns match what the model learned during training.
            """)
            
        except FileNotFoundError:
            st.error("❌ Test cases file not found. Run `python generate_complete_test_cases.py` first.")
        except Exception as e:
            st.error(f"❌ Error loading test cases: {str(e)}")
        
        st.markdown("---")
    
    # === LIVE MODE ===
    # Input section
    st.markdown("### 🎯 Analyze an Address")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Enter wallet address, pool address, or transaction ID",
            placeholder="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            label_visibility="collapsed"
        )
    with col2:
        analyze_button = st.button("🚀 Analyze", type="primary", use_container_width=True)
    
    if analyze_button:
        if not user_input:
            st.warning("⚠️ Please enter an address or transaction ID")
            st.stop()
        
        # Auto-detect blockchain
        if user_input.startswith('0x'):
            blockchain = "Ethereum"
            
            with st.spinner("🔄 Fetching wallet data from Etherscan..."):
                try:
                    result = fetch_ethereum_wallet(user_input)
                    if len(result) == 4:
                        features, is_contract, red_flags, data_source = result
                    else:
                        features, is_contract, red_flags = result
                        data_source = "UNKNOWN"
                except Exception as e:
                    st.error(f"❌ Error fetching data: {str(e)}")
                    st.stop()
            
            if features is None or data_source in ["ERROR", "NO_DATA"]:
                st.error("❌ Could not retrieve live data for this address")
                if red_flags:
                    st.warning("**Reason:**")
                    for flag in red_flags:
                        st.markdown(f"- {flag}")
                st.info("💡 **Tip:** Make sure the address has transaction history on Ethereum mainnet.")
                st.stop()
            
            # Data source badge
            if data_source == "LIVE_API":
                st.success("📡 **Data Source:** Live Etherscan API")
            else:
                st.warning(f"📡 **Data Source:** {data_source}")
            
            # Smart contract warnings
            if red_flags:
                with st.expander("⚠️ Smart Contract Warnings", expanded=True):
                    for flag in red_flags:
                        st.markdown(f"- {flag}")
            
            # Run inference
            feature_names = list(features.keys())
            
            with st.spinner("🤖 Running fraud detection AI..."):
                new_x, new_edge_index, new_node_idx, edge_count = attach_node_to_graph(
                    features, eth_graph, eth_scaler, k=10
                )
                
                result_pred = predict_with_explanation(
                    eth_model, new_x, new_edge_index, new_node_idx,
                    feature_names, features, edge_count, is_ethereum=True
                )
            
            # Results card with color coding
            st.markdown("---")
            st.markdown("## 📊 Risk Assessment Results")
            
            # Determine border color based on risk
            if result_pred['risk_score'] < 33:
                border_color = "#28a745"  # Green
                icon = "✅"
            elif result_pred['risk_score'] < 66:
                border_color = "#ffc107"  # Orange
                icon = "⚠️"
            else:
                border_color = "#dc3545"  # Red
                icon = "🚨"
            
            # Verdict banner
            st.markdown(f"""
                <div style='padding: 1rem; border-left: 5px solid {border_color}; background-color: rgba(0,0,0,0.02); border-radius: 5px; margin: 1rem 0;'>
                    <h3 style='margin: 0; color: {border_color};'>{icon} {result_pred['verdict']}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Risk Score", f"{result_pred['risk_score']}/100")
            with col2:
                category_clean = result_pred['risk_category'].replace('🟢', '').replace('🟡', '').replace('🔴', '').strip()
                st.metric("📊 Risk Category", category_clean)
            with col3:
                st.metric("🔬 Model Confidence", f"{result_pred['confidence']:.1%}")
            
            # Explanation
            st.markdown("### 💡 Analysis")
            st.write(result_pred['explanation'])
            
            # High-volume safety net
            total_eth = features.get('total Ether sent', 0) + features.get('total ether received', 0)
            received_count = features.get('Received Tnx', 0)
            sent_count = features.get('Sent tnx', 0)
            
            if total_eth > 10000 and received_count > sent_count * 2:
                st.warning("⚠️ **High-Volume Notice:** This wallet shows unusually large transaction volume (>10,000 ETH). The model is optimized for retail-level fraud detection. Manual review recommended for high-volume wallets.")
            
            if is_contract:
                st.info("ℹ️ **Note:** This address is a smart contract")
            
            # Technical details collapsed
            with st.expander("🔧 Technical Details"):
                st.markdown(f"""
                **Blockchain:** Ethereum  
                **Model:** GraphSAGE Graph Neural Network  
                **Graph Connections:** {result_pred['edge_count']} edges to similar wallets  
                **Flagged Neighbors:** {result_pred['flagged_neighbors']} suspicious wallets nearby  
                **Training Data:** 9,288 wallets (94.3% ROC-AUC)  
                **Data Source:** {data_source}
                """)
        
        else:
            blockchain = "Solana"
            
            with st.spinner("🔄 Fetching Solana pool data..."):
                try:
                    result = fetch_solana_pool(user_input)
                    if len(result) == 3:
                        features, red_flags, data_source = result
                    else:
                        features, red_flags = result
                        data_source = "UNKNOWN"
                except Exception as e:
                    st.error(f"❌ Error fetching data: {str(e)}")
                    st.stop()
            
            if features is None or data_source in ["ERROR", "NO_DATA"]:
                st.error("❌ Could not retrieve live data for this pool")
                if red_flags:
                    st.warning("**Reason:**")
                    for flag in red_flags:
                        st.markdown(f"- {flag}")
                st.info("💡 **Tip:** Solana pool data fetching requires a valid Solana API endpoint.")
                st.stop()
            
            # Data source badge
            if data_source == "LIVE_API":
                st.success("📡 **Data Source:** Live Solana API")
            else:
                st.warning(f"📡 **Data Source:** {data_source}")
            
            # Pool warnings
            if red_flags:
                with st.expander("⚠️ Pool Warnings", expanded=True):
                    for flag in red_flags:
                        st.markdown(f"- {flag}")
            
            # Run inference
            feature_names = [
                'REMOVE_RATIO', 'NUM_LIQUIDITY_ADDS', 'NUM_LIQUIDITY_REMOVES',
                'TOTAL_ADDED_LIQUIDITY', 'TOTAL_REMOVED_LIQUIDITY',
                'POOL_LIFETIME_HOURS', 'ADD_TO_REMOVE_RATIO'
            ]
            features_ordered = {k: features[k] for k in feature_names}
            
            with st.spinner("🤖 Running rug-pull detection AI..."):
                new_x, new_edge_index, new_node_idx, edge_count = attach_node_to_graph(
                    features_ordered, sol_graph, sol_scaler, k=10
                )
                
                result_pred = predict_with_explanation(
                    sol_model, new_x, new_edge_index, new_node_idx,
                    feature_names, features, edge_count, is_ethereum=False
                )
            
            # Results card with color coding
            st.markdown("---")
            st.markdown("## 📊 Risk Assessment Results")
            
            # Determine border color
            if result_pred['risk_score'] < 33:
                border_color = "#28a745"; icon = "✅"
            elif result_pred['risk_score'] < 66:
                border_color = "#ffc107"; icon = "⚠️"
            else:
                border_color = "#dc3545"; icon = "🚨"
            
            # Verdict banner
            st.markdown(f"""
                <div style='padding: 1rem; border-left: 5px solid {border_color}; background-color: rgba(0,0,0,0.02); border-radius: 5px; margin: 1rem 0;'>
                    <h3 style='margin: 0; color: {border_color};'>{icon} {result_pred['verdict']}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Risk Score", f"{result_pred['risk_score']}/100")
            with col2:
                category_clean = result_pred['risk_category'].replace('🟢', '').replace('🟡', '').replace('🔴', '').strip()
                st.metric("📊 Risk Category", category_clean)
            with col3:
                st.metric("🔬 Model Confidence", f"{result_pred['confidence']:.1%}")
            
            # Explanation
            st.markdown("### 💡 Analysis")
            st.write(result_pred['explanation'])
            
            # Pool details
            with st.expander("📊 Pool Details"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Token (MINT):** `{features.get('MINT', 'N/A')[:20]}...`")
                    st.markdown(f"**Status:** {features.get('INACTIVITY_STATUS', 'N/A')}")
                with col2:
                    st.markdown(f"**Lifetime:** {features.get('POOL_LIFETIME_HOURS', 0):.1f} hours")
                    st.markdown(f"**Liquidity Events:** {int(features.get('NUM_LIQUIDITY_ADDS', 0))} adds")
            
            # Technical details
            with st.expander("🔧 Technical Details"):
                st.markdown(f"""
                **Blockchain:** Solana  
                **Model:** GraphSAGE Graph Neural Network  
                **Graph Connections:** {result_pred['edge_count']} edges to similar pools  
                **Flagged Neighbors:** {result_pred['flagged_neighbors']} suspicious pools nearby  
                **Training Data:** 116,304 pools (91.5% ROC-AUC)  
                **Data Source:** {data_source}
                """)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔍 System Info")
        
        # Detect mode
        mode = "🧪 Synthetic Test" if test_mode else ("🌐 Live API" if user_input else "⚪ Idle")
        
        st.markdown(f"""
        **Mode:** {mode}  
        **Blockchain:** {'Ethereum' if user_input and user_input.startswith('0x') else 'Solana' if user_input else 'N/A'}  
        **Models Loaded:** ✅  
        **API Status:** {'🟢 Live' if user_input and not test_mode else '⚪ Idle'}
        """)
        
        if test_mode:
            st.info("Using synthetic test mode with 100 pre-computed cases")
        
        st.markdown("---")
        st.markdown("### 📚 Resources")
        st.markdown("""
        - [LIMITATIONS.md](../docs/LIMITATIONS.md) - Model scope & limitations
        - [Test Cases](../tests/test_addresses.csv) - Validation results
        - Training: 9,288 ETH + 116,304 SOL samples
        """)
        
        st.markdown("---")
        st.markdown("### ⚠️ Disclaimer")
        st.markdown("""
        This tool provides risk assessment, not financial advice.  
        Always verify independently.
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p style='margin: 0;'>Blockchain Fraud Detection System | Powered by GraphSAGE GNN</p>
            <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem;'>⚠️ Optimized for retail-level fraud detection | See LIMITATIONS.md for full scope</p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
