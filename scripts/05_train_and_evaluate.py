"""
COMPREHENSIVE TRAINING AND EVALUATION PIPELINE

Trains and evaluates multiple model variants on the same untouched test set.
Includes log1p transformation, validation set carving, and proper threshold selection.

Models:
(i) GraphSAGE - 38 features, no augmentation
(iii) GraphSAGE - 22 non-ERC20 features, no augmentation
Plus: Logistic Regression and Random Forest on both feature sets
Plus: Shuffled-label test on best GNN

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
print("COMPREHENSIVE TRAINING AND EVALUATION")
print("="*80)

# ============================================================================
# PART 1: DATA PREPARATION WITH LOG1P TRANSFORMATION
# ============================================================================

print("\n[1/6] Loading and preparing data...")
train_full = pd.read_csv('data/splits/ethereum/train.csv')
test_df = pd.read_csv('data/splits/ethereum/test.csv')

all_features = [col for col in train_full.columns if col not in ['Address', 'FLAG']]
non_erc20_features = [col for col in all_features if 'ERC20' not in col and 'ERC 20' not in col]

print(f"  Original train: {len(train_full):,} rows")
print(f"  Test (untouched): {len(test_df):,} rows")
print(f"  All features: {len(all_features)}")
print(f"  Non-ERC20 features: {len(non_erc20_features)}")

# Carve out 15% validation from ORIGINAL train (before any augmentation)
print("\n[2/6] Creating stratified train/val split (85/15)...")
train_df, val_df = train_test_split(
    train_full,
    test_size=0.15,
    random_state=42,
    stratify=train_full['FLAG']
)

print(f"  Train: {len(train_df):,} ({(train_df['FLAG']==1).sum()} fraud, {(train_df['FLAG']==0).sum()} legit)")
print(f"  Val: {len(val_df):,} ({(val_df['FLAG']==1).sum()} fraud, {(val_df['FLAG']==0).sum()} legit)")
print(f"  Test: {len(test_df):,} ({(test_df['FLAG']==1).sum()} fraud, {(test_df['FLAG']==0).sum()} legit)")

def apply_log1p_transform(df, feature_cols):
    """Apply signed log1p to all features (handles negative values)"""
    df_transformed = df.copy()
    for col in feature_cols:
        df_transformed[col] = np.sign(df[col]) * np.log1p(np.abs(df[col]))
    return df_transformed

print("\n[3/6] Applying log1p transformation...")
train_log = apply_log1p_transform(train_df, all_features)
val_log = apply_log1p_transform(val_df, all_features)
test_log = apply_log1p_transform(test_df, all_features)

print("  ✓ Applied signed log1p to all value/count columns")

# ============================================================================
# PART 2: BUILD GRAPHS FOR BOTH FEATURE SETS
# ============================================================================

def build_transductive_graph(train_data, val_data, test_data, feature_cols, k=10):
    """
    Build transductive k-NN similarity graph.
    
    CRITICAL: Labels from val and test are NOT used during training.
    Only feature similarity determines edges.
    """
    # Extract features and labels
    X_train = train_data[feature_cols].values
    X_val = val_data[feature_cols].values
    X_test = test_data[feature_cols].values
    
    y_train = train_data['FLAG'].values
    y_val = val_data['FLAG'].values
    y_test = test_data['FLAG'].values
    
    # Fit scaler on TRAIN only
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Combine for graph (transductive learning)
    X_all = np.vstack([X_train_scaled, X_val_scaled, X_test_scaled])
    y_all = np.concatenate([y_train, y_val, y_test])
    
    # Build k-NN similarity graph
    adj_matrix = kneighbors_graph(
        X_all, n_neighbors=k, mode='connectivity', 
        include_self=False, n_jobs=-1
    )
    edge_index = torch.LongTensor(np.array(adj_matrix.nonzero()))
    
    # Create PyTorch Geometric Data
    x = torch.FloatTensor(X_all)
    y = torch.LongTensor(y_all)
    data = Data(x=x, edge_index=edge_index, y=y)
    
    # Create masks
    n_train = len(X_train)
    n_val = len(X_val)
    n_test = len(X_test)
    
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

print("\n[4/6] Building transductive k-NN similarity graphs...")
print("  Graph type: Transductive (all nodes visible, but only train labels used)")

# Build both variants
data_38feat, scaler_38feat = build_transductive_graph(
    train_log, val_log, test_log, all_features, k=10
)
print(f"  ✓ 38 features: {data_38feat.x.shape[0]} nodes, {data_38feat.edge_index.shape[1]} edges")

data_22feat, scaler_22feat = build_transductive_graph(
    train_log, val_log, test_log, non_erc20_features, k=10
)
print(f"  ✓ 22 features: {data_22feat.x.shape[0]} nodes, {data_22feat.edge_index.shape[1]} edges")

# Prepare data for sklearn models
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

# ============================================================================
# PART 3: DEFINE GRAPHSAGE MODEL
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

# ============================================================================
# PART 4: TRAINING FUNCTIONS
# ============================================================================

def train_gnn(data, epochs=200, lr=0.01):
    """
    Train GNN with early stopping on validation.
    CRITICAL: Only train_mask labels are used in loss.
    """
    model = GraphSAGE(data.num_features, 64, 2, dropout=0.4)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    
    # Class weights from train set only
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
        
        # Loss computed ONLY on train_mask
        loss = F.nll_loss(out[data.train_mask], data.y[data.train_mask], weight=class_weights)
        loss.backward()
        optimizer.step()
        
        # Validate every 10 epochs
        if epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                out = model(data.x, data.edge_index)
                pred = out.argmax(dim=1)
                prob = torch.exp(out)[:, 1]
                
                val_pred = pred[data.val_mask].numpy()
                val_true = data.y[data.val_mask].numpy()
                val_prob = prob[data.val_mask].numpy()
                
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
            
            if patience_counter >= 3:  # Check every 10 epochs
                break
    
    # Load best model
    model.load_state_dict(best_state)
    return model, best_epoch

def evaluate_model_with_threshold(model, data, mask, val_mask=None):
    """
    Evaluate model and find optimal threshold on validation set.
    Returns metrics on the specified mask.
    """
    model.eval()
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        prob = torch.exp(out)[:, 1]
    
    # Find optimal threshold on validation set
    if val_mask is not None:
        val_prob = prob[val_mask].numpy()
        val_true = data.y[val_mask].numpy()
        fpr, tpr, thresholds = roc_curve(val_true, val_prob)
        # Optimal threshold: maximize F1
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
    else:
        best_threshold = 0.5
    
    # Evaluate on target mask with chosen threshold
    prob_np = prob[mask].numpy()
    true_np = data.y[mask].numpy()
    pred_np = (prob_np >= best_threshold).astype(int)
    
    acc = accuracy_score(true_np, pred_np)
    prec, rec, f1, _ = precision_recall_fscore_support(
        true_np, pred_np, average='binary', zero_division=0
    )
    roc_auc = roc_auc_score(true_np, prob_np)
    cm = confusion_matrix(true_np, pred_np)
    
    return {
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1': f1,
        'roc_auc': roc_auc,
        'confusion_matrix': cm,
        'threshold': best_threshold
    }

# ============================================================================
# PART 5: TRAIN ALL MODELS
# ============================================================================

print("\n[5/6] Training models...")
results = []

# (i) GraphSAGE - 38 features
print("\n  Training GNN (38 features)...")
model_38, epoch_38 = train_gnn(data_38feat)
metrics_38 = evaluate_model_with_threshold(
    model_38, data_38feat, data_38feat.test_mask, data_38feat.val_mask
)
results.append(('GNN-38feat', metrics_38))
print(f"    Best epoch: {epoch_38}, Test F1: {metrics_38['f1']:.4f}")

# (iii) GraphSAGE - 22 features (no ERC20)
print("\n  Training GNN (22 features, no ERC20)...")
model_22, epoch_22 = train_gnn(data_22feat)
metrics_22 = evaluate_model_with_threshold(
    model_22, data_22feat, data_22feat.test_mask, data_22feat.val_mask
)
results.append(('GNN-22feat (no ERC20)', metrics_22))
print(f"    Best epoch: {epoch_22}, Test F1: {metrics_22['f1']:.4f}")

# Logistic Regression - 38 features
print("\n  Training Logistic Regression (38 features)...")
lr_38 = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
lr_38.fit(X_train_38_scaled, y_train)
lr_38_pred = lr_38.predict(X_test_38_scaled)
lr_38_prob = lr_38.predict_proba(X_test_38_scaled)[:, 1]
lr_38_metrics = {
    'accuracy': accuracy_score(y_test, lr_38_pred),
    'precision': precision_recall_fscore_support(y_test, lr_38_pred, average='binary', zero_division=0)[0],
    'recall': precision_recall_fscore_support(y_test, lr_38_pred, average='binary', zero_division=0)[1],
    'f1': precision_recall_fscore_support(y_test, lr_38_pred, average='binary', zero_division=0)[2],
    'roc_auc': roc_auc_score(y_test, lr_38_prob),
    'confusion_matrix': confusion_matrix(y_test, lr_38_pred),
    'threshold': 0.5  # Default for sklearn
}
results.append(('LogReg-38feat', lr_38_metrics))
print(f"    Test F1: {lr_38_metrics['f1']:.4f}")

# Logistic Regression - 22 features
print("\n  Training Logistic Regression (22 features, no ERC20)...")
lr_22 = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
lr_22.fit(X_train_22_scaled, y_train)
lr_22_pred = lr_22.predict(X_test_22_scaled)
lr_22_prob = lr_22.predict_proba(X_test_22_scaled)[:, 1]
lr_22_metrics = {
    'accuracy': accuracy_score(y_test, lr_22_pred),
    'precision': precision_recall_fscore_support(y_test, lr_22_pred, average='binary', zero_division=0)[0],
    'recall': precision_recall_fscore_support(y_test, lr_22_pred, average='binary', zero_division=0)[1],
    'f1': precision_recall_fscore_support(y_test, lr_22_pred, average='binary', zero_division=0)[2],
    'roc_auc': roc_auc_score(y_test, lr_22_prob),
    'confusion_matrix': confusion_matrix(y_test, lr_22_pred),
    'threshold': 0.5
}
results.append(('LogReg-22feat (no ERC20)', lr_22_metrics))
print(f"    Test F1: {lr_22_metrics['f1']:.4f}")

# Random Forest - 38 features
print("\n  Training Random Forest (38 features)...")
rf_38 = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced', n_jobs=-1)
rf_38.fit(X_train_38_scaled, y_train)
rf_38_pred = rf_38.predict(X_test_38_scaled)
rf_38_prob = rf_38.predict_proba(X_test_38_scaled)[:, 1]
rf_38_metrics = {
    'accuracy': accuracy_score(y_test, rf_38_pred),
    'precision': precision_recall_fscore_support(y_test, rf_38_pred, average='binary', zero_division=0)[0],
    'recall': precision_recall_fscore_support(y_test, rf_38_pred, average='binary', zero_division=0)[1],
    'f1': precision_recall_fscore_support(y_test, rf_38_pred, average='binary', zero_division=0)[2],
    'roc_auc': roc_auc_score(y_test, rf_38_prob),
    'confusion_matrix': confusion_matrix(y_test, rf_38_pred),
    'threshold': 0.5
}
results.append(('RandomForest-38feat', rf_38_metrics))
print(f"    Test F1: {rf_38_metrics['f1']:.4f}")

# Random Forest - 22 features
print("\n  Training Random Forest (22 features, no ERC20)...")
rf_22 = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced', n_jobs=-1)
rf_22.fit(X_train_22_scaled, y_train)
rf_22_pred = rf_22.predict(X_test_22_scaled)
rf_22_prob = rf_22.predict_proba(X_test_22_scaled)[:, 1]
rf_22_metrics = {
    'accuracy': accuracy_score(y_test, rf_22_pred),
    'precision': precision_recall_fscore_support(y_test, rf_22_pred, average='binary', zero_division=0)[0],
    'recall': precision_recall_fscore_support(y_test, rf_22_pred, average='binary', zero_division=0)[1],
    'f1': precision_recall_fscore_support(y_test, rf_22_pred, average='binary', zero_division=0)[2],
    'roc_auc': roc_auc_score(y_test, rf_22_prob),
    'confusion_matrix': confusion_matrix(y_test, rf_22_pred),
    'threshold': 0.5
}
results.append(('RandomForest-22feat (no ERC20)', rf_22_metrics))
print(f"    Test F1: {rf_22_metrics['f1']:.4f}")

# ============================================================================
# PART 6: SHUFFLED LABEL TEST (on better GNN)
# ============================================================================

print("\n[6/6] Shuffled-label test on better GNN...")
better_gnn = model_38 if metrics_38['f1'] > metrics_22['f1'] else model_22
better_data = data_38feat if metrics_38['f1'] > metrics_22['f1'] else data_22feat
better_name = "38feat" if metrics_38['f1'] > metrics_22['f1'] else "22feat"

# Shuffle train labels
data_shuffled = better_data.clone()
train_indices = torch.where(data_shuffled.train_mask)[0]
shuffled_labels = data_shuffled.y[train_indices][torch.randperm(len(train_indices))]
data_shuffled.y[train_indices] = shuffled_labels

print(f"  Training GNN with SHUFFLED labels ({better_name})...")
model_shuffled, _ = train_gnn(data_shuffled, epochs=100)
metrics_shuffled = evaluate_model_with_threshold(
    model_shuffled, data_shuffled, data_shuffled.test_mask, data_shuffled.val_mask
)
print(f"    Shuffled ROC-AUC: {metrics_shuffled['roc_auc']:.4f} (should be ~0.5)")

# ============================================================================
# PRINT RESULTS TABLE
# ============================================================================

print("\n" + "="*80)
print("EVALUATION RESULTS - ALL MODELS ON SAME TEST SET")
print("="*80)

print(f"\n{'Model':<30} {'Acc':<8} {'Prec':<8} {'Rec':<8} {'F1':<8} {'ROC-AUC':<8} {'Thresh':<8}")
print("-" * 80)
for name, metrics in results:
    print(f"{name:<30} {metrics['accuracy']:.4f}   {metrics['precision']:.4f}   "
          f"{metrics['recall']:.4f}   {metrics['f1']:.4f}   {metrics['roc_auc']:.4f}   "
          f"{metrics['threshold']:.4f}")

print(f"\nShuffled-label test ({better_name}): ROC-AUC = {metrics_shuffled['roc_auc']:.4f}")

print("\n" + "="*80)
print("CONFUSION MATRICES")
print("="*80)
for name, metrics in results:
    print(f"\n{name}:")
    print(f"  [[TN={metrics['confusion_matrix'][0,0]:4d}  FP={metrics['confusion_matrix'][0,1]:4d}]")
    print(f"   [FN={metrics['confusion_matrix'][1,0]:4d}  TP={metrics['confusion_matrix'][1,1]:4d}]]")

print("\n" + "="*80)
print("NOTES")
print("="*80)
print("- Graph type: Transductive k-NN similarity graph (k=10)")
print("- Validation set: 15% of original train, used for threshold selection")
print("- Test set: Completely untouched, evaluated once")
print("- Log1p transformation applied to all features before scaling")
print("- GNN training uses ONLY train_mask labels in loss computation")
print("- Val/test labels never used in training, scaling, or message passing")
