"""
Analyze why the known phishing address gets Low Risk (0/100)
Address: 0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8
Expected: High Risk (70-100)
Actual: Low Risk (0/100)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.live.fetch_ethereum import fetch_ethereum_wallet
import numpy as np
import pickle
import torch
from sklearn.neighbors import NearestNeighbors

print("="*80)
print("ANALYZING KNOWN PHISHING ADDRESS")
print("="*80)
print("Address: 0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8")
print("Expected Risk: 70-100 (High Risk - Known Phishing)")
print("="*80)

# Fetch features
print("\n[STEP 1] Fetching features from Etherscan...")
features, is_contract, flags, source = fetch_ethereum_wallet('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8')

if not features:
    print("ERROR: Could not fetch features")
    sys.exit(1)

print(f"\n✓ Features extracted: {len(features)}")
print(f"✓ Data source: {source}")

# Analyze fraud indicators
print("\n[STEP 2] Analyzing Fraud Indicators...")
print("-"*80)

sent = features.get('Sent tnx', 0)
received = features.get('Received Tnx', 0)
unique_sent = features.get('Unique Sent To Addresses', 0)
unique_received = features.get('Unique Received From Addresses', 0)
total_sent = features.get('total Ether sent', 0)
total_received = features.get('total ether received', 0)
balance = features.get('total ether balance', 0)
avg_sent = features.get('avg val sent', 0)
avg_received = features.get('avg val received', 0)

print(f"Transaction Counts:")
print(f"  Sent:     {sent:.0f} transactions")
print(f"  Received: {received:.0f} transactions")
print(f"  Ratio:    {sent/max(received, 1):.2f}x (sent/received)")

print(f"\nNetwork Activity:")
print(f"  Unique addresses sent to:      {unique_sent:.0f}")
print(f"  Unique addresses received from: {unique_received:.0f}")
print(f"  Dispersion ratio: {unique_sent/max(unique_received, 1):.2f}x")

print(f"\nETH Volume:")
print(f"  Total sent:     {total_sent:.4f} ETH")
print(f"  Total received: {total_received:.4f} ETH")
print(f"  Final balance:  {balance:.4f} ETH")

print(f"\nAverage Transaction Size:")
print(f"  Avg sent:     {avg_sent:.6f} ETH")
print(f"  Avg received: {avg_received:.6f} ETH")

# FRAUD PATTERN DETECTION
print("\n[STEP 3] Fraud Pattern Analysis...")
print("-"*80)

fraud_indicators = []

# Pattern 1: High send-to-receive ratio (typical of scams)
if sent > received * 5:
    fraud_indicators.append(f"🚨 SCAM PATTERN: Sends {sent/max(received,1):.1f}x more than receives (typical of phishing/scams)")

# Pattern 2: Many unique recipients (distribution pattern)
if unique_sent > 100:
    fraud_indicators.append(f"🚨 DISTRIBUTION PATTERN: Sends to {unique_sent:.0f} unique addresses (typical of stolen fund distribution)")

# Pattern 3: High dispersion (sends to many, receives from few)
if unique_sent > unique_received * 3:
    fraud_indicators.append(f"🚨 DISPERSION: Sends to {unique_sent/max(unique_received,1):.1f}x more addresses than receives from")

# Pattern 4: Near-zero balance (drains everything)
if balance < 0.01 and total_received > 1:
    fraud_indicators.append(f"🚨 DRAINED: Received {total_received:.2f} ETH but balance is {balance:.4f} ETH (typical drain)")

# Pattern 5: Small average sends (distributing stolen funds)
if avg_sent < 0.1 and sent > 100:
    fraud_indicators.append(f"🚨 MICRO-SENDS: Average send is only {avg_sent:.6f} ETH across {sent:.0f} txs (typical distribution)")

if fraud_indicators:
    print("FRAUD INDICATORS DETECTED:")
    for indicator in fraud_indicators:
        print(f"  {indicator}")
else:
    print("⚠ NO FRAUD INDICATORS DETECTED BY RULES")

# Load model and predict
print("\n[STEP 4] GNN Model Prediction...")
print("-"*80)

# Load model
checkpoint = torch.load('models/ethereum_clean/gnn_22feat.pt', weights_only=False)
with open('models/ethereum_clean/scaler_22feat.pkl', 'rb') as f:
    scaler = pickle.load(f)
train_features = np.load('models/ethereum_clean/train_features_22.npy')
feature_list = checkpoint['feature_list']

# Prepare features
feature_vector = np.array([features.get(f, 0.0) for f in feature_list])
print(f"Feature vector (22 features):")
for i, (name, value) in enumerate(zip(feature_list[:5], feature_vector[:5])):
    print(f"  {name}: {value:.4f}")
print(f"  ... and {len(feature_list)-5} more features")

# Transform
feature_vector_log = np.sign(feature_vector) * np.log1p(np.abs(feature_vector))
features_scaled = scaler.transform(feature_vector_log.reshape(1, -1))[0]

print(f"\nAfter log1p + scaling:")
print(f"  Min: {features_scaled.min():.4f}")
print(f"  Max: {features_scaled.max():.4f}")
print(f"  Mean: {features_scaled.mean():.4f}")
print(f"  Std: {features_scaled.std():.4f}")

# Find neighbors
knn = NearestNeighbors(n_neighbors=10, metric='euclidean')
knn.fit(train_features)
distances, indices = knn.kneighbors([features_scaled])

print(f"\nNearest neighbors in training data:")
print(f"  Distances: {distances[0][:3]}")
print(f"  Training node indices: {indices[0][:3]}")

# Build graph and predict
from src.app import GraphSAGE

model = GraphSAGE(22, 64, 2, 0.4)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

new_node_idx = train_features.shape[0]
edge_list = []

# Connect to neighbors
for neighbor_idx in indices[0]:
    edge_list.append([new_node_idx, neighbor_idx])
    edge_list.append([neighbor_idx, new_node_idx])

# Connect neighbors
for i, idx1 in enumerate(indices[0]):
    for idx2 in indices[0][i+1:]:
        edge_list.append([idx1, idx2])
        edge_list.append([idx2, idx1])

x_all = np.vstack([train_features, features_scaled])
x_tensor = torch.FloatTensor(x_all)
edge_index = torch.LongTensor(edge_list).t()

with torch.no_grad():
    out = model(x_tensor, edge_index)
    probs = torch.exp(out)[new_node_idx]
    fraud_prob = probs[1].item()

risk_score = int(fraud_prob * 100)

print(f"\n[RESULT] Model Prediction:")
print(f"  Fraud probability: {fraud_prob:.4f}")
print(f"  Risk score: {risk_score}/100")
print(f"  Class: {'🚨 HIGH RISK' if risk_score >= 70 else '⚠ MEDIUM RISK' if risk_score >= 33 else '✅ LOW RISK'}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)

# Final verdict
print("\n[VERDICT]")
if risk_score >= 70:
    print("✓ CORRECT: Model correctly identifies this as high risk")
elif risk_score >= 33:
    print("⚠ PARTIAL: Model shows medium risk, but should be high")
else:
    print("✗ FALSE NEGATIVE: Model shows low risk for known phishing address!")
    print("\nPOSSIBLE CAUSES:")
    print("1. Model trained on 2017 data, phishing patterns evolved")
    print("2. Model relies on graph structure, but phishing address neighbors are diverse")
    print("3. Feature scaling may normalize suspicious patterns")
    print("4. Model may need retraining with 2024 phishing examples")

print("\n[RECOMMENDATIONS]")
print("1. ADD BLACKLIST: Integrate Etherscan phishing database")
print("2. ADD RULES: Supplement GNN with rule-based fraud detection")
print("3. RETRAIN: Include 2024 phishing addresses in training data")
print("4. ENSEMBLE: Combine GNN + Rules + Blacklist for final score")
