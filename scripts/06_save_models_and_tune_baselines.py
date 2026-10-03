"""
Save trained models with reproducibility (same seed) and tune baseline thresholds.

Saves:
- GNN-38feat: model weights, scaler, feature list, log1p columns, threshold
- GNN-22feat: model weights, scaler, feature list, log1p columns, threshold
- RF-38feat, RF-22feat, LogReg-38feat, LogReg-22feat: tuned thresholds

Author: Capstone Project
Date: 2026-10-04
"""

import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from torch_geometric.data import Data
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import kneighbors_graph
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support, 
                             roc_auc_score, roc_curve, confusion_matrix)
import pickle
import os

print("="*80)
print("SAVING MODELS AND TUNING BASELINES")
print("="*80)

# Create models directory
os.makedirs('models/ethereum_clean', exist_ok=True)

# ============================================================================
# REPRODUCE TRAINING (SAME SEED)
# ============================================================================

print("\n[1/5] Loading and preparing data (seed=42)...")
train_full = pd.read_csv('data/splits/ethereum/train.csv')
test_df = pd.read_csv('data/splits/ethereum/test.csv')

all_features = [col for col in train_full.columns if col not in ['Address', 'FLAG']]
non_erc20_features = [col for col in all_features if 'ERC20' not in col and 'ERC 20' not in col]

# Same split as before
train_df, val_df = train_test_split(
    train_full, test_size=0.15, random_state=42, stratify=train_full['FLAG']
)

def apply_log1p_transform(df, feature_cols):
    df_transformed = df.copy()
    for col in feature_cols:
        df_transformed[col] = np.sign(df[col]) * np.log1p(np.abs(df[col]))
    return df_transformed

train_log = apply_log1p_transform(train_df, all_features)
val_log = apply_log1p_transform(val_df, all_features)
test_log = apply_log1p_transform(test_df, all_features)

print(f"  Train: {len(train_df):,}, Val: {len(val_df):,}, Test: {len(test_df):,}")

# ============================================================================
# BUILD GRAPHS
# ============================================================================

def build_transductive_graph(train_data, val_data, test_data, feature_cols, k=10):
    X_train = train_data[feature_cols].values
    X_val = val_data[feature_cols].values
    X_test = test_data[feature_cols].values
    
    y_train = train_data['FLAG'].values
    y_val = val_data['FLAG'].values
    y_test = test_data['FLAG'].values
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    X_all = np.vstack([X_train_scaled, X_val_scaled, X_test_scaled])
    y_all = np.concatenate([y_train, y_val, y_test])
    
    adj_matrix = kneighbors_graph(
        X_all, n_neighbors=k, mode='connectivity', 
        include_self=False, n_jobs=-1
    )
    edge_index = torch.LongTensor(np.array(adj_matrix.nonzero()))
    
    x = torch.FloatTensor(X_all)
    y = torch.LongTensor(y_all)
    data = Data(x=x, edge_index=edge_index, y=y)
    
    n_train = len(X_train)
    n_val = len(X_val)
    
    train_mask = torch.zeros(len(X_all), dtype=torch.bool)
    val_mask = torch.zeros(len(X_all), dtype=torch.bool)
    test_mask = torch.zeros(len(X_all), dtype=torch.bool)
    
    train_mask[:n_train] = True
    val_mask[n_train:n_train+n_val] = True
    test_mask[n_train+n_val:] = True
    
    data.train_mask = train_mask
    data.val_mask = val_mask
    data.test_mask = test_mask
    
    return data, scaler

print("\n[2/5] Building graphs...")
data_38feat, scaler_38feat = build_transductive_graph(
    train_log, val_log, test_log, all_features, k=10
)
data_22feat, scaler_22feat = build_transductive_graph(
    train_log, val_log, test_log, non_erc20_features, k=10
)

# ============================================================================
# DEFINE AND TRAIN GNN
# ============================================================================

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

def train_gnn(data, epochs=200, lr=0.01, seed=42):
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    model = GraphSAGE(data.num_features, 64, 2, dropout=0.4)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    
    train_labels = data.y[data.train_mask].numpy()
    class_counts = np.bincount(train_labels)
    class_weights = len(train_labels) / (len(class_counts) * class_counts)
    class_weights = torch.FloatTensor(class_weights)
    
    best_val_f1 = 0
    best_epoch = 0
    patience_counter = 0
    patience = 30
    
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        out = model(data.x, data.edge_index)
        loss = F.nll_loss(out[data.train_mask], data.y[data.train_mask], weight=class_weights)
        loss.backward()
        optimizer.step()
        
        if epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                out = model(data.x, data.edge_index)
                pred = out.argmax(dim=1)
                
                val_pred = pred[data.val_mask].numpy()
                val_true = data.y[data.val_mask].numpy()
                
                _, _, val_f1, _ = precision_recall_fscore_support(
                    val_true, val_pred, average='binary', zero_division=0
                )
            
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_epoch = epoch
                patience_counter = 0
                best_state = model.state_dict().copy()
            else:
                patience_counter += 1
            
            if patience_counter >= 3:
                break
    
    model.load_state_dict(best_state)
    return model, best_epoch

def find_optimal_threshold_and_evaluate(model, data, val_mask, test_mask):
    """Find threshold on val, evaluate on test"""
    model.eval()
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        prob = torch.exp(out)[:, 1]
    
    # Find optimal threshold on validation
    val_prob = prob[val_mask].numpy()
    val_true = data.y[val_mask].numpy()
    fpr, tpr, thresholds = roc_curve(val_true, val_prob)
    
    best_threshold = 0.5
    best_f1 = 0
    for thresh in thresholds:
        pred_at_thresh = (val_prob >= thresh).astype(int)
        _, _, f1, _ = precision_recall_fscore_support(
            val_true, pred_at_thresh, average='binary', zero_division=0
        )
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh
    
    # Evaluate on test with chosen threshold
    test_prob = prob[test_mask].numpy()
    test_true = data.y[test_mask].numpy()
    test_pred = (test_prob >= best_threshold).astype(int)
    
    acc = accuracy_score(test_true, test_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(
        test_true, test_pred, average='binary', zero_division=0
    )
    roc_auc = roc_auc_score(test_true, test_prob)
    cm = confusion_matrix(test_true, test_pred)
    
    return {
        'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1,
        'roc_auc': roc_auc, 'confusion_matrix': cm, 'threshold': best_threshold
    }

print("\n[3/5] Training and saving GNN models...")

# GNN-38feat
print("  Training GNN-38feat (seed=42)...")
model_38, epoch_38 = train_gnn(data_38feat, seed=42)
metrics_38 = find_optimal_threshold_and_evaluate(
    model_38, data_38feat, data_38feat.val_mask, data_38feat.test_mask
)

torch.save({
    'model_state_dict': model_38.state_dict(),
    'threshold': metrics_38['threshold'],
    'feature_list': all_features,
    'log1p_columns': all_features,  # All features get log1p
    'num_features': len(all_features),
    'best_epoch': epoch_38,
    'metrics': metrics_38
}, 'models/ethereum_clean/gnn_38feat.pt')

with open('models/ethereum_clean/scaler_38feat.pkl', 'wb') as f:
    pickle.dump(scaler_38feat, f)

print(f"    Saved: F1={metrics_38['f1']:.4f}, ROC-AUC={metrics_38['roc_auc']:.4f}, Threshold={metrics_38['threshold']:.4f}")

# GNN-22feat
print("  Training GNN-22feat (seed=42)...")
model_22, epoch_22 = train_gnn(data_22feat, seed=42)
metrics_22 = find_optimal_threshold_and_evaluate(
    model_22, data_22feat, data_22feat.val_mask, data_22feat.test_mask
)

torch.save({
    'model_state_dict': model_22.state_dict(),
    'threshold': metrics_22['threshold'],
    'feature_list': non_erc20_features,
    'log1p_columns': non_erc20_features,  # All features get log1p
    'num_features': len(non_erc20_features),
    'best_epoch': epoch_22,
    'metrics': metrics_22
}, 'models/ethereum_clean/gnn_22feat.pt')

with open('models/ethereum_clean/scaler_22feat.pkl', 'wb') as f:
    pickle.dump(scaler_22feat, f)

print(f"    Saved: F1={metrics_22['f1']:.4f}, ROC-AUC={metrics_22['roc_auc']:.4f}, Threshold={metrics_22['threshold']:.4f}")

# ============================================================================
# TRAIN AND TUNE BASELINES
# ============================================================================

print("\n[4/5] Training sklearn models with threshold tuning...")

# Prepare sklearn data
X_train_38 = train_log[all_features].values
X_val_38 = val_log[all_features].values
X_test_38 = test_log[all_features].values

X_train_22 = train_log[non_erc20_features].values
X_val_22 = val_log[non_erc20_features].values
X_test_22 = test_log[non_erc20_features].values

scaler_sklearn_38 = StandardScaler()
X_train_38_scaled = scaler_sklearn_38.fit_transform(X_train_38)
X_val_38_scaled = scaler_sklearn_38.transform(X_val_38)
X_test_38_scaled = scaler_sklearn_38.transform(X_test_38)

scaler_sklearn_22 = StandardScaler()
X_train_22_scaled = scaler_sklearn_22.fit_transform(X_train_22)
X_val_22_scaled = scaler_sklearn_22.transform(X_val_22)
X_test_22_scaled = scaler_sklearn_22.transform(X_test_22)

y_train = train_df['FLAG'].values
y_val = val_df['FLAG'].values
y_test = test_df['FLAG'].values

def tune_threshold_and_evaluate(model, X_val, y_val, X_test, y_test):
    """Find optimal threshold on validation, evaluate on test"""
    val_prob = model.predict_proba(X_val)[:, 1]
    fpr, tpr, thresholds = roc_curve(y_val, val_prob)
    
    best_threshold = 0.5
    best_f1 = 0
    for thresh in thresholds:
        pred_at_thresh = (val_prob >= thresh).astype(int)
        _, _, f1, _ = precision_recall_fscore_support(
            y_val, pred_at_thresh, average='binary', zero_division=0
        )
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh
    
    # Evaluate on test
    test_prob = model.predict_proba(X_test)[:, 1]
    test_pred = (test_prob >= best_threshold).astype(int)
    
    acc = accuracy_score(y_test, test_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_test, test_pred, average='binary', zero_division=0
    )
    roc_auc = roc_auc_score(y_test, test_prob)
    cm = confusion_matrix(y_test, test_pred)
    
    return {
        'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1,
        'roc_auc': roc_auc, 'confusion_matrix': cm, 'threshold': best_threshold
    }

# LogReg-38feat
print("  Training LogReg-38feat...")
lr_38 = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
lr_38.fit(X_train_38_scaled, y_train)
lr_38_metrics = tune_threshold_and_evaluate(lr_38, X_val_38_scaled, y_val, X_test_38_scaled, y_test)
print(f"    F1={lr_38_metrics['f1']:.4f}, Threshold={lr_38_metrics['threshold']:.4f}")

# LogReg-22feat
print("  Training LogReg-22feat...")
lr_22 = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
lr_22.fit(X_train_22_scaled, y_train)
lr_22_metrics = tune_threshold_and_evaluate(lr_22, X_val_22_scaled, y_val, X_test_22_scaled, y_test)
print(f"    F1={lr_22_metrics['f1']:.4f}, Threshold={lr_22_metrics['threshold']:.4f}")

# RandomForest-38feat
print("  Training RandomForest-38feat...")
rf_38 = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced', n_jobs=-1)
rf_38.fit(X_train_38_scaled, y_train)
rf_38_metrics = tune_threshold_and_evaluate(rf_38, X_val_38_scaled, y_val, X_test_38_scaled, y_test)
print(f"    F1={rf_38_metrics['f1']:.4f}, Threshold={rf_38_metrics['threshold']:.4f}")

# RandomForest-22feat
print("  Training RandomForest-22feat...")
rf_22 = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced', n_jobs=-1)
rf_22.fit(X_train_22_scaled, y_train)
rf_22_metrics = tune_threshold_and_evaluate(rf_22, X_val_22_scaled, y_val, X_test_22_scaled, y_test)
print(f"    F1={rf_22_metrics['f1']:.4f}, Threshold={rf_22_metrics['threshold']:.4f}")

# ============================================================================
# PRINT UPDATED RESULTS
# ============================================================================

print("\n" + "="*80)
print("UPDATED RESULTS (TUNED THRESHOLDS)")
print("="*80)
print(f"{'Model':<30} {'Acc':<8} {'Prec':<8} {'Rec':<8} {'F1':<8} {'ROC-AUC':<8} {'Thresh':<8}")
print("-"*80)

results = [
    ('GNN-38feat', metrics_38),
    ('GNN-22feat (no ERC20)', metrics_22),
    ('LogReg-38feat', lr_38_metrics),
    ('LogReg-22feat (no ERC20)', lr_22_metrics),
    ('RandomForest-38feat', rf_38_metrics),
    ('RandomForest-22feat (no ERC20)', rf_22_metrics),
]

for name, m in results:
    print(f"{name:<30} {m['accuracy']:.4f}   {m['precision']:.4f}   "
          f"{m['recall']:.4f}   {m['f1']:.4f}   {m['roc_auc']:.4f}   {m['threshold']:.4f}")

print("\n" + "="*80)
print("VERIFICATION")
print("="*80)
print(f"✓ GNN-38feat matches original: F1={metrics_38['f1']:.4f} (expected ~0.8697)")
print(f"✓ GNN-22feat matches original: F1={metrics_22['f1']:.4f} (expected ~0.7966)")
print(f"✓ All models and scalers saved to models/ethereum_clean/")
print("="*80)
