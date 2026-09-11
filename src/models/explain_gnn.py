"""
STEP 7: GNN Explainability using Gradient-based Feature Importance
Explain individual node predictions with feature importance and neighbor context
(Using gradient-based method instead of GNNExplainer for scalability)
"""

import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
import pandas as pd
import numpy as np
import os


class GraphSAGE(torch.nn.Module):
    """GraphSAGE model (must match training architecture)"""
    def __init__(self, in_channels, hidden_channels, out_channels, dropout=0.5):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)
        self.dropout = dropout
    
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)


def load_model_and_graph(dataset_name):
    """Load trained model and graph data"""
    # Load graph
    graph_path = f'data/processed/{dataset_name}_graph.pt'
    data = torch.load(graph_path, weights_only=False)
    
    # Load model
    model = GraphSAGE(
        in_channels=data.num_features,
        hidden_channels=128,
        out_channels=2,
        dropout=0.5
    )
    
    model_path = f'models/{dataset_name}/model.pt'
    model.load_state_dict(torch.load(model_path, weights_only=True))
    model.eval()
    
    return model, data


def explain_node(model, data, node_id, dataset_name='ethereum'):
    """
    Explain a single node prediction using gradient-based feature importance
    (Faster alternative to GNNExplainer for large graphs)
    """
    try:
        model.eval()
        
        # Clone data to avoid modifying original
        x = data.x.clone().detach().requires_grad_(True)
        
        # Get prediction
        out = model(x, data.edge_index)
        pred_class = out[node_id].argmax().item()
        pred_prob = torch.exp(out[node_id])[pred_class].item()
        
        # Compute gradients w.r.t. input features for this node
        model.zero_grad()
        if x.grad is not None:
            x.grad.zero_()
        
        out[node_id, pred_class].backward(retain_graph=False)
        
        # Feature importance = absolute gradient values
        feature_importance = torch.abs(x.grad[node_id])
        top_features_idx = torch.topk(feature_importance, k=min(5, len(feature_importance))).indices.tolist()
        top_features_scores = feature_importance[top_features_idx].tolist()
        
        # Find important neighbors (1-hop neighbors with same predicted class)
        neighbors = data.edge_index[1, data.edge_index[0] == node_id].tolist()
        important_neighbors = []
        
        if len(neighbors) > 0:
            with torch.no_grad():
                out_full = model(data.x, data.edge_index)
                neighbor_preds = out_full[neighbors].argmax(dim=1)
                neighbor_labels = data.y[neighbors]
            
            # Select top 5 neighbors predicted as same class
            same_class_neighbors = [(n, data.y[n].item(), 1.0) 
                                    for n, pred in zip(neighbors, neighbor_preds) 
                                    if pred == pred_class]
            important_neighbors = same_class_neighbors[:5]
        
        return {
            'node_id': node_id,
            'predicted_class': pred_class,
            'confidence': pred_prob,
            'true_label': data.y[node_id].item(),
            'top_features': list(zip(top_features_idx, top_features_scores)),
            'important_neighbors': important_neighbors,
            'node_features': data.x[node_id].detach().tolist()
        }
    except Exception as e:
        print(f"Error explaining node {node_id}: {e}")
        # Return basic prediction without explanation
        with torch.no_grad():
            out = model(data.x, data.edge_index)
            pred_class = out[node_id].argmax().item()
            pred_prob = torch.exp(out[node_id])[pred_class].item()
        
        return {
            'node_id': node_id,
            'predicted_class': pred_class,
            'confidence': pred_prob,
            'true_label': data.y[node_id].item(),
            'top_features': [(i, 0.0) for i in range(min(5, data.num_features))],
            'important_neighbors': [],
            'node_features': data.x[node_id].tolist()
        }


def generate_explanation_text(explanation, dataset_name):
    """Convert explanation to plain English"""
    pred_class = explanation['predicted_class']
    confidence = explanation['confidence']
    
    if dataset_name == 'ethereum':
        # Load feature names
        df = pd.read_csv('data/processed/ethereum_clean.csv', nrows=1)
        feature_names = [col for col in df.columns if col != 'FLAG']
        
        class_name = "FRAUD" if pred_class == 1 else "LEGITIMATE"
        
        text = f"Prediction: {class_name} (confidence: {confidence:.1%})\n\n"
        text += "Why this prediction?\n"
        
        # Top features
        text += "\nKey behavioral patterns detected:\n"
        for feat_idx, score in explanation['top_features'][:3]:
            if feat_idx < len(feature_names):
                feat_name = feature_names[feat_idx]
                feat_value = explanation['node_features'][feat_idx]
                text += f"  • {feat_name}: {feat_value:.4f} (importance: {score:.3f})\n"
        
        # Network context
        if explanation['important_neighbors']:
            fraud_neighbors = sum(1 for _, label, _ in explanation['important_neighbors'] if label == 1)
            total_neighbors = len(explanation['important_neighbors'])
            text += f"\nNetwork context:\n"
            text += f"  • Connected to {total_neighbors} influential wallets\n"
            text += f"  • {fraud_neighbors} of them are flagged as fraudulent\n"
    
    else:  # solana
        feature_names = [
            'REMOVE_RATIO',
            'NUM_LIQUIDITY_ADDS',
            'NUM_LIQUIDITY_REMOVES',
            'TOTAL_ADDED_LIQUIDITY',
            'TOTAL_REMOVED_LIQUIDITY',
            'POOL_LIFETIME_HOURS',
            'ADD_TO_REMOVE_RATIO'
        ]
        
        class_name = "RUG-PULL" if pred_class == 1 else "LEGITIMATE"
        
        text = f"Prediction: {class_name} (confidence: {confidence:.1%})\n\n"
        text += "Why this prediction?\n"
        
        # Top features with context
        text += "\nKey liquidity patterns:\n"
        for feat_idx, score in explanation['top_features'][:3]:
            if feat_idx < len(feature_names):
                feat_name = feature_names[feat_idx]
                feat_value = explanation['node_features'][feat_idx]
                
                if 'REMOVE_RATIO' in feat_name:
                    text += f"  • {feat_name}: {feat_value:.2f} (importance: {score:.3f})\n"
                    text += f"    → {'High' if feat_value > 0.85 else 'Normal'} liquidity removal relative to deposits\n"
                elif 'LIFETIME' in feat_name:
                    text += f"  • Pool active for {feat_value:.1f} hours (importance: {score:.3f})\n"
                else:
                    text += f"  • {feat_name}: {feat_value:.4f} (importance: {score:.3f})\n"
        
        # Network context
        if explanation['important_neighbors']:
            rugpull_neighbors = sum(1 for _, label, _ in explanation['important_neighbors'] if label == 1)
            total_neighbors = len(explanation['important_neighbors'])
            text += f"\nToken ecosystem context:\n"
            text += f"  • Shares token (MINT) with {total_neighbors} other pools\n"
            text += f"  • {rugpull_neighbors} of those pools are flagged as rug-pulls\n"
    
    return text


def generate_example_explanations():
    """Generate example explanations for each class"""
    print("=" * 80)
    print("GENERATING EXAMPLE EXPLANATIONS")
    print("=" * 80)
    
    output_lines = []
    
    # Ethereum examples
    print("\n📊 ETHEREUM EXAMPLES")
    model_eth, data_eth = load_model_and_graph('ethereum')
    
    # Load test set
    test_df_eth = pd.read_csv('data/splits/ethereum/test.csv')
    
    # Find one fraud and one legit example from test set
    fraud_example = test_df_eth[test_df_eth['label'] == 1]['node_idx'].iloc[0]
    legit_example = test_df_eth[test_df_eth['label'] == 0]['node_idx'].iloc[0]
    
    print(f"  Explaining fraud node: {fraud_example}")
    fraud_exp = explain_node(model_eth, data_eth, fraud_example, 'ethereum')
    fraud_text = generate_explanation_text(fraud_exp, 'ethereum')
    
    print(f"  Explaining legitimate node: {legit_example}")
    legit_exp = explain_node(model_eth, data_eth, legit_example, 'ethereum')
    legit_text = generate_explanation_text(legit_exp, 'ethereum')
    
    output_lines.append("=" * 80)
    output_lines.append("ETHEREUM WALLET FRAUD DETECTION - EXAMPLE EXPLANATIONS")
    output_lines.append("=" * 80)
    output_lines.append("\n--- EXAMPLE 1: FRAUD WALLET ---")
    output_lines.append(f"Node ID: {fraud_example}")
    output_lines.append(f"True Label: {'FRAUD' if fraud_exp['true_label'] == 1 else 'LEGITIMATE'}")
    output_lines.append(fraud_text)
    output_lines.append("\n--- EXAMPLE 2: LEGITIMATE WALLET ---")
    output_lines.append(f"Node ID: {legit_example}")
    output_lines.append(f"True Label: {'FRAUD' if legit_exp['true_label'] == 1 else 'LEGITIMATE'}")
    output_lines.append(legit_text)
    
    # Solana examples
    print("\n🏊 SOLANA EXAMPLES")
    model_sol, data_sol = load_model_and_graph('solana')
    
    # Load test set
    test_df_sol = pd.read_csv('data/splits/solana/test.csv')
    
    # Find one rugpull and one legit example
    rugpull_example = test_df_sol[test_df_sol['label'] == 1]['node_idx'].iloc[0]
    legit_pool_example = test_df_sol[test_df_sol['label'] == 0]['node_idx'].iloc[0]
    
    print(f"  Explaining rug-pull node: {rugpull_example}")
    rugpull_exp = explain_node(model_sol, data_sol, rugpull_example, 'solana')
    rugpull_text = generate_explanation_text(rugpull_exp, 'solana')
    
    print(f"  Explaining legitimate node: {legit_pool_example}")
    legit_pool_exp = explain_node(model_sol, data_sol, legit_pool_example, 'solana')
    legit_pool_text = generate_explanation_text(legit_pool_exp, 'solana')
    
    output_lines.append("\n\n")
    output_lines.append("=" * 80)
    output_lines.append("SOLANA LIQUIDITY POOL RUG-PULL DETECTION - EXAMPLE EXPLANATIONS")
    output_lines.append("=" * 80)
    output_lines.append("\n--- EXAMPLE 1: RUG-PULL POOL ---")
    output_lines.append(f"Node ID: {rugpull_example}")
    output_lines.append(f"True Label: {'RUG-PULL' if rugpull_exp['true_label'] == 1 else 'LEGITIMATE'}")
    output_lines.append(rugpull_text)
    output_lines.append("\n--- EXAMPLE 2: LEGITIMATE POOL ---")
    output_lines.append(f"Node ID: {legit_pool_example}")
    output_lines.append(f"True Label: {'RUG-PULL' if legit_pool_exp['true_label'] == 1 else 'LEGITIMATE'}")
    output_lines.append(legit_pool_text)
    
    # Save to file
    os.makedirs('results', exist_ok=True)
    output_path = 'results/example_explanations.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\n✅ Example explanations saved: {output_path}")
    
    # Print to console
    print("\n" + "\n".join(output_lines))
    
    return output_path


if __name__ == "__main__":
    generate_example_explanations()
    
    print("\n" + "=" * 80)
    print("✅ STEP 7 COMPLETE - Explainability finished")
    print("=" * 80)
