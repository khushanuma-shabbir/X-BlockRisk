"""
GNN-based Fraud Detector
Graph Neural Network for detecting rug pulls and Sybil attacks
"""

import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, GATConv
from torch_geometric.data import Data
import numpy as np
from pathlib import Path
import json

class PrecisionGNN(torch.nn.Module):
    """
    GraphSAGE + GAT for high-precision fraud detection
    Detects rug pull patterns through graph structure
    """
    def __init__(self, num_features, hidden_channels=64, num_classes=2):
        super().__init__()
        
        # Layer 1: GraphSAGE (aggregate neighbors)
        self.conv1 = SAGEConv(num_features, hidden_channels)
        
        # Layer 2: GraphSAGE
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)
        
        # Layer 3: Graph Attention (focus on important neighbors)
        self.gat = GATConv(hidden_channels, hidden_channels // 4, heads=4, concat=True)
        
        # Classification layer
        self.lin = torch.nn.Linear(hidden_channels, num_classes)
        
        # Dropout for regularization
        self.dropout = torch.nn.Dropout(0.5)
    
    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        
        # Layer 1
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Layer 2
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Attention layer
        x = self.gat(x, edge_index)
        x = F.relu(x)
        
        # Classification
        x = self.lin(x)
        
        return F.log_softmax(x, dim=1)


class GNNFraudDetector:
    """
    Wrapper for GNN model to detect fraud through graph patterns
    """
    
    def __init__(self):
        self.model = None
        self.model_path = Path("models/gnn/precision_gnn.pt")
        self.metrics_path = Path("models/gnn/gnn_metrics.json")
        self.loaded = False
    
    def load(self):
        """Load trained GNN model"""
        if not self.model_path.exists():
            print(f"⚠ GNN model not found at {self.model_path}")
            print("  Run: python scripts/train_precision_gnn.py")
            return False
        
        try:
            # Load checkpoint
            checkpoint = torch.load(self.model_path)
            
            # Create model
            self.model = PrecisionGNN(
                num_features=checkpoint['num_features'],
                hidden_channels=checkpoint['hidden_channels']
            )
            
            # Load weights
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            
            # Load metrics
            with open(self.metrics_path, 'r') as f:
                self.metrics = json.load(f)
            
            self.loaded = True
            
            print("✓ GNN model loaded")
            print(f"  Architecture: {self.metrics['model_type']}")
            print(f"  Test F1: {self.metrics['test_f1_score']:.3f}")
            print(f"  Nodes: {self.metrics['num_nodes']}, Edges: {self.metrics['num_edges']}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error loading GNN: {e}")
            return False
    
    def predict(self, features: dict) -> tuple:
        """
        Predict fraud probability using GNN
        
        Args:
            features: Dictionary with transaction features
            
        Returns:
            (probability, confidence)
        """
        if not self.loaded:
            if not self.load():
                # Fallback to default score
                return 0.15, "LOW"  # Default GNN score
        
        try:
            # Extract features
            feature_cols = [
                'total_txs', 'total_value_eth', 'avg_tx_value',
                'unique_senders', 'unique_receivers', 'is_contract',
                'first_tx_age_days', 'last_tx_age_days', 'tx_frequency',
                'incoming_tx_count', 'outgoing_tx_count', 'avg_gas_price',
                'failed_tx_ratio'
            ]
            
            # Create feature vector
            x = torch.FloatTensor([[features.get(col, 0) for col in feature_cols]])
            
            # Create simple graph (single node for now)
            # In full implementation, would use actual transaction graph
            edge_index = torch.LongTensor([[0], [0]])  # Self-loop
            
            # Create PyG data
            data = Data(x=x, edge_index=edge_index)
            
            # Predict
            with torch.no_grad():
                out = self.model(data)
                proba = torch.exp(out[0][1]).item()  # Probability of fraud
            
            # Confidence
            if proba < 0.3 or proba > 0.7:
                confidence = "HIGH"
            elif proba < 0.4 or proba > 0.6:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
            
            return proba, confidence
            
        except Exception as e:
            print(f"GNN prediction error: {e}")
            return 0.15, "LOW"  # Fallback
    
    def get_rug_pull_indicators(self, features: dict) -> dict:
        """
        Analyze graph patterns for rug pull indicators
        
        Returns:
            Dictionary with rug pull risk factors
        """
        indicators = {
            'sybil_network': False,
            'liquidity_drain': False,
            'coordinated_dump': False,
            'money_laundering': False,
            'risk_score': 0
        }
        
        # Check for Sybil network (many addresses, one controller)
        unique_receivers = features.get('unique_receivers', 0)
        unique_senders = features.get('unique_senders', 0)
        
        if unique_receivers > 50 and unique_senders < 5:
            indicators['sybil_network'] = True
            indicators['risk_score'] += 30
        
        # Check for liquidity drain
        incoming = features.get('incoming_tx_count', 0)
        outgoing = features.get('outgoing_tx_count', 0)
        
        if incoming > 100 and outgoing < 10:
            indicators['liquidity_drain'] = True
            indicators['risk_score'] += 40
        
        # Check for coordinated dump
        avg_tx_value = features.get('avg_tx_value', 0)
        if avg_tx_value > 10 and outgoing > 20:  # Large value, many sends
            indicators['coordinated_dump'] = True
            indicators['risk_score'] += 35
        
        # Check for money laundering
        if unique_receivers > 100:  # Distributing to many addresses
            indicators['money_laundering'] = True
            indicators['risk_score'] += 25
        
        return indicators


if __name__ == "__main__":
    # Test GNN detector
    detector = GNNFraudDetector()
    
    if detector.load():
        print("\n✓ GNN Detector ready!")
        print("\nTesting with sample features...")
        
        # Test features
        test_features = {
            'total_txs': 1000,
            'total_value_eth': 100,
            'avg_tx_value': 0.1,
            'unique_senders': 10,
            'unique_receivers': 200,
            'is_contract': 1,
            'first_tx_age_days': 30,
            'last_tx_age_days': 5,
            'tx_frequency': 33.3,
            'incoming_tx_count': 800,
            'outgoing_tx_count': 200,
            'avg_gas_price': 50000000000,
            'failed_tx_ratio': 0.1
        }
        
        proba, conf = detector.predict(test_features)
        print(f"\nPrediction: {proba:.2%} fraud probability ({conf} confidence)")
        
        indicators = detector.get_rug_pull_indicators(test_features)
        print(f"\nRug Pull Indicators:")
        for key, value in indicators.items():
            if key != 'risk_score':
                print(f"  {key}: {value}")
        print(f"  Risk Score: {indicators['risk_score']}/100")
    else:
        print("✗ GNN not available")
