"""
STEP 6: Train GraphSAGE GNN Models
Train GNN for both Ethereum and Solana with class-weighted loss
"""

import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from torch_geometric.data import Data
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os


class GraphSAGE(torch.nn.Module):
    """GraphSAGE model (2-layer)"""
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


def train_epoch(model, data, train_mask, optimizer, class_weights):
    """Single training epoch"""
    model.train()
    optimizer.zero_grad()
    
    out = model(data.x, data.edge_index)
    loss = F.nll_loss(out[train_mask], data.y[train_mask], weight=class_weights)
    
    loss.backward()
    optimizer.step()
    
    return loss.item()


@torch.no_grad()
def evaluate(model, data, mask):
    """Evaluate model on given mask"""
    model.eval()
    out = model(data.x, data.edge_index)
    pred = out.argmax(dim=1)
    
    y_true = data.y[mask].cpu().numpy()
    y_pred = pred[mask].cpu().numpy()
    y_prob = torch.exp(out[mask])[:, 1].cpu().numpy()  # Probability of positive class
    
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary', zero_division=0)
    
    try:
        roc_auc = roc_auc_score(y_true, y_prob)
    except:
        roc_auc = 0.0
    
    return acc, prec, rec, f1, roc_auc, y_true, y_pred


def train_model(graph_path, dataset_name, splits_dir, output_dir, epochs=200, hidden_dim=128, lr=0.01):
    """
    Train GraphSAGE model with class-weighted loss
    """
    print("=" * 80)
    print(f"{dataset_name.upper()} - GNN TRAINING")
    print("=" * 80)
    
    # Load graph
    data = torch.load(graph_path, weights_only=False)
    
    # Load splits
    train_df = pd.read_csv(f'{splits_dir}/train.csv')
    val_df = pd.read_csv(f'{splits_dir}/val.csv')
    test_df = pd.read_csv(f'{splits_dir}/test.csv')
    
    train_idx = train_df['node_idx'].values
    val_idx = val_df['node_idx'].values
    test_idx = test_df['node_idx'].values
    
    # Create masks
    train_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    
    train_mask[train_idx] = True
    val_mask[val_idx] = True
    test_mask[test_idx] = True
    
    print(f"\n📊 Dataset: {dataset_name}")
    print(f"   Nodes: {data.num_nodes:,}")
    print(f"   Edges: {data.num_edges:,}")
    print(f"   Features: {data.num_features}")
    print(f"   Train samples: {train_mask.sum():,}")
    print(f"   Val samples: {val_mask.sum():,}")
    print(f"   Test samples: {test_mask.sum():,}")
    
    # Compute class weights (inverse frequency)
    train_labels = data.y[train_mask].numpy()
    class_counts = np.bincount(train_labels)
    class_weights = len(train_labels) / (len(class_counts) * class_counts)
    class_weights = torch.FloatTensor(class_weights)
    
    print(f"\n⚖️  Class weights: {class_weights.tolist()}")
    print(f"   (addresses class imbalance: {class_counts})")
    
    # Initialize model
    model = GraphSAGE(
        in_channels=data.num_features,
        hidden_channels=hidden_dim,
        out_channels=2,  # Binary classification
        dropout=0.5
    )
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    
    # Training loop
    print(f"\n🚀 Training for {epochs} epochs...")
    best_val_f1 = 0
    best_epoch = 0
    patience = 30
    patience_counter = 0
    
    for epoch in range(1, epochs + 1):
        loss = train_epoch(model, data, train_mask, optimizer, class_weights)
        
        if epoch % 10 == 0:
            val_acc, val_prec, val_rec, val_f1, val_roc, _, _ = evaluate(model, data, val_mask)
            
            print(f"Epoch {epoch:3d} | Loss: {loss:.4f} | Val F1: {val_f1:.4f} | Val ROC-AUC: {val_roc:.4f}")
            
            # Early stopping based on F1 score
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_epoch = epoch
                patience_counter = 0
                # Save best model
                torch.save(model.state_dict(), f'{output_dir}/model_best.pt')
            else:
                patience_counter += 1
            
            if patience_counter >= patience // 10:  # Check every 10 epochs
                print(f"\n⏸️  Early stopping at epoch {epoch} (best: {best_epoch})")
                break
    
    # Load best model
    model.load_state_dict(torch.load(f'{output_dir}/model_best.pt', weights_only=True))
    
    # Final evaluation on test set
    print(f"\n{'=' * 80}")
    print("📈 FINAL TEST SET EVALUATION")
    print("=" * 80)
    
    test_acc, test_prec, test_rec, test_f1, test_roc, y_true, y_pred = evaluate(model, data, test_mask)
    
    print(f"\nAccuracy:  {test_acc:.4f}")
    print(f"Precision: {test_prec:.4f}")
    print(f"Recall:    {test_rec:.4f}")
    print(f"F1-Score:  {test_f1:.4f}")
    print(f"ROC-AUC:   {test_roc:.4f}")
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    print(f"\nConfusion Matrix:")
    print(cm)
    
    # Save confusion matrix plot
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f'{dataset_name.capitalize()} GNN - Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    cm_path = f'results/confusion_matrices/{dataset_name}_gnn_confusion_matrix.png'
    os.makedirs(os.path.dirname(cm_path), exist_ok=True)
    plt.savefig(cm_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\n✅ Confusion matrix saved: {cm_path}")
    
    # Save evaluation report
    report_path = f'results/evaluation_reports/{dataset_name}_gnn_report.txt'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(f"{dataset_name.upper()} GraphSAGE GNN - TEST SET EVALUATION\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Accuracy:  {test_acc:.4f}\n")
        f.write(f"Precision: {test_prec:.4f}\n")
        f.write(f"Recall:    {test_rec:.4f}\n")
        f.write(f"F1-Score:  {test_f1:.4f}\n")
        f.write(f"ROC-AUC:   {test_roc:.4f}\n\n")
        f.write(f"Confusion Matrix:\n{cm}\n\n")
        f.write(f"Best epoch: {best_epoch}\n")
    print(f"✅ Evaluation report saved: {report_path}")
    
    # Save final model
    final_model_path = f'{output_dir}/model.pt'
    torch.save(model.state_dict(), final_model_path)
    print(f"✅ Final model saved: {final_model_path}")
    
    # Check for suspiciously high/low performance
    if test_roc > 0.99:
        print(f"\n⚠️  WARNING: Suspiciously high ROC-AUC ({test_roc:.4f}) - possible data leakage!")
    elif test_roc < 0.55:
        print(f"\n⚠️  WARNING: Suspiciously low ROC-AUC ({test_roc:.4f}) - model may not be learning!")
    
    return {
        'accuracy': test_acc,
        'precision': test_prec,
        'recall': test_rec,
        'f1': test_f1,
        'roc_auc': test_roc
    }


if __name__ == "__main__":
    print("🚀 Starting GNN training for both datasets...\n")
    
    # Train Ethereum model
    eth_metrics = train_model(
        graph_path='data/processed/ethereum_graph.pt',
        dataset_name='ethereum',
        splits_dir='data/splits/ethereum',
        output_dir='models/ethereum',
        epochs=200,
        hidden_dim=128,
        lr=0.01
    )
    
    print("\n\n")
    
    # Train Solana model
    sol_metrics = train_model(
        graph_path='data/processed/solana_graph.pt',
        dataset_name='solana',
        splits_dir='data/splits/solana',
        output_dir='models/solana',
        epochs=200,
        hidden_dim=128,
        lr=0.01
    )
    
    print("\n\n")
    print("=" * 80)
    print("🎯 FINAL RESULTS SUMMARY")
    print("=" * 80)
    print(f"\nETHEREUM:")
    print(f"  Accuracy:  {eth_metrics['accuracy']:.4f}")
    print(f"  F1-Score:  {eth_metrics['f1']:.4f}")
    print(f"  ROC-AUC:   {eth_metrics['roc_auc']:.4f}")
    
    print(f"\nSOLANA:")
    print(f"  Accuracy:  {sol_metrics['accuracy']:.4f}")
    print(f"  F1-Score:  {sol_metrics['f1']:.4f}")
    print(f"  ROC-AUC:   {sol_metrics['roc_auc']:.4f}")
    
    print("\n" + "=" * 80)
    print("✅ STEP 6 COMPLETE - GNN training finished")
    print("=" * 80)
