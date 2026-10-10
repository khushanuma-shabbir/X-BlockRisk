"""
Analyze existing GNN training data quality
"""

import torch
import pandas as pd
import os

print("="*80)
print("📊 ANALYZING EXISTING GNN DATA")
print("="*80)

# ============================================================================
# 1. Check ML Training CSV
# ============================================================================

print("\n[1/3] ML Training Data (CSV)...")

csv_path = 'data/ml_training/ethereum_training_data.csv'
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    
    print(f"  File: {csv_path}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Features: {list(df.columns)}")
    
    if 'label' in df.columns:
        fraud = (df['label'] == 1).sum()
        legit = (df['label'] == 0).sum()
        print(f"\n  Labels:")
        print(f"    Fraud: {fraud} ({fraud/len(df)*100:.1f}%)")
        print(f"    Legit: {legit} ({legit/len(df)*100:.1f}%)")
        
        balance = min(fraud, legit) / max(fraud, legit) if max(fraud, legit) > 0 else 0
        print(f"    Balance ratio: {balance:.3f}")
        
        if balance < 0.5:
            print(f"    ⚠️ IMBALANCED!")
        else:
            print(f"    ✅ Good balance")
    
    # Check for missing values
    missing = df.isnull().sum().sum()
    print(f"\n  Missing values: {missing}")
    
    # Sample addresses
    if 'address' in df.columns:
        print(f"\n  Sample addresses:")
        for addr in df['address'].head(3):
            label = df[df['address'] == addr]['label'].values[0]
            print(f"    {addr} - {'FRAUD' if label == 1 else 'LEGIT'}")
else:
    print(f"  ❌ Not found: {csv_path}")

# ============================================================================
# 2. Check Graph Files (.pt)
# ============================================================================

print("\n[2/3] PyTorch Graph Files (.pt)...")

graph_files = [
    'data/processed/ethereum_graph_clean.pt',
    'data/processed/ethereum_graph_augmented.pt',
    'data/processed/ethereum_graph_no_aug.pt',
    'data/processed/ethereum_graph_no_erc20.pt'
]

best_graph = None
best_score = 0

for graph_path in graph_files:
    if os.path.exists(graph_path):
        try:
            # Fix PyTorch 2.6 weights_only warning
            data = torch.load(graph_path, weights_only=False)
            
            size_mb = os.path.getsize(graph_path) / (1024 * 1024)
            
            print(f"\n  File: {os.path.basename(graph_path)}")
            print(f"  Size: {size_mb:.2f} MB")
            
            if hasattr(data, 'x'):
                print(f"  Nodes: {data.x.shape[0]}")
                print(f"  Features per node: {data.x.shape[1]}")
            
            if hasattr(data, 'edge_index'):
                print(f"  Edges: {data.edge_index.shape[1]}")
            
            if hasattr(data, 'y'):
                print(f"  Labels: {data.y.shape[0]}")
                
                fraud = (data.y == 1).sum().item()
                legit = (data.y == 0).sum().item()
                print(f"    Fraud: {fraud}")
                print(f"    Legit: {legit}")
                
                balance = min(fraud, legit) / max(fraud, legit) if max(fraud, legit) > 0 else 0
                print(f"    Balance: {balance:.3f}")
            
            # Calculate quality score
            if hasattr(data, 'x') and hasattr(data, 'edge_index') and hasattr(data, 'y'):
                nodes = data.x.shape[0]
                edges = data.edge_index.shape[1]
                features = data.x.shape[1]
                
                # Score based on: nodes, edges, features, balance
                score = nodes + edges/10 + features * 100
                if hasattr(data, 'y'):
                    fraud = (data.y == 1).sum().item()
                    legit = (data.y == 0).sum().item()
                    balance = min(fraud, legit) / max(fraud, legit) if max(fraud, legit) > 0 else 0
                    score *= (1 + balance)
                
                print(f"  Quality Score: {score:.0f}")
                
                if score > best_score:
                    best_score = score
                    best_graph = graph_path
        
        except Exception as e:
            print(f"  ❌ Error loading: {e}")
    else:
        print(f"  ⚠️ Not found: {graph_path}")

# ============================================================================
# 3. Final Assessment
# ============================================================================

print("\n[3/3] Final Assessment...")
print("="*80)

# Load best graph for detailed analysis
if best_graph:
    print(f"\n🏆 BEST GRAPH: {os.path.basename(best_graph)}")
    
    data = torch.load(best_graph, weights_only=False)
    
    nodes = data.x.shape[0] if hasattr(data, 'x') else 0
    edges = data.edge_index.shape[1] if hasattr(data, 'edge_index') else 0
    features = data.x.shape[1] if hasattr(data, 'x') else 0
    
    print(f"\n📊 GRAPH STRUCTURE:")
    print(f"   Nodes: {nodes}")
    print(f"   Edges: {edges}")
    print(f"   Features: {features}")
    print(f"   Avg degree: {edges/nodes:.1f}")
    
    if hasattr(data, 'y'):
        fraud = (data.y == 1).sum().item()
        legit = (data.y == 0).sum().item()
        balance = min(fraud, legit) / max(fraud, legit) if max(fraud, legit) > 0 else 0
        
        print(f"\n📊 LABELS:")
        print(f"   Fraud: {fraud}")
        print(f"   Legit: {legit}")
        print(f"   Balance: {balance:.3f}")
    
    # Quality assessment
    print(f"\n🎯 QUALITY ASSESSMENT:")
    
    if nodes < 100:
        print(f"   ❌ TOO FEW NODES (need 1000+)")
        quality = "POOR"
    elif nodes < 1000:
        print(f"   ⚠️ LIMITED NODES (aim for 5000+)")
        quality = "FAIR"
    elif nodes < 5000:
        print(f"   ✅ DECENT NODES")
        quality = "GOOD"
    else:
        print(f"   🎉 EXCELLENT NODE COUNT")
        quality = "EXCELLENT"
    
    if edges < nodes * 5:
        print(f"   ⚠️ SPARSE GRAPH (edges/node ratio: {edges/nodes:.1f})")
    else:
        print(f"   ✅ GOOD CONNECTIVITY")
    
    if features < 10:
        print(f"   ⚠️ FEW FEATURES (aim for 50+)")
    elif features < 30:
        print(f"   ✅ DECENT FEATURES")
    else:
        print(f"   🎉 RICH FEATURE SET")
    
    if hasattr(data, 'y'):
        if balance < 0.2:
            print(f"   ❌ HIGHLY IMBALANCED")
            quality = "POOR"
        elif balance < 0.5:
            print(f"   ⚠️ IMBALANCED (use class weights)")
        else:
            print(f"   ✅ BALANCED LABELS")
    
    print(f"\n{'='*80}")
    print(f"OVERALL QUALITY: {quality}")
    print(f"{'='*80}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if quality == "POOR":
        print(f"   ❌ Current data NOT suitable for strong GNN")
        print(f"   ")
        print(f"   NEED:")
        print(f"   - More addresses (current: {nodes}, need: 1000+)")
        print(f"   - Build 3-hop transaction graph")
        print(f"   - Extract 50+ features per node")
        print(f"   ")
        print(f"   SOLUTION:")
        print(f"   1. Use final_dataset.csv (5904 fraud + 1032 legit)")
        print(f"   2. Build 3-hop graph: python scripts/build_3hop_graph.py")
        print(f"   3. Extract features: python scripts/extract_features.py")
        print(f"   4. Train GNN: python scripts/train_strong_gnn.py")
    
    elif quality == "FAIR":
        print(f"   ⚠️ Can train but accuracy will be limited")
        print(f"   ")
        print(f"   CURRENT: {nodes} nodes")
        print(f"   RECOMMENDED: 5000+ nodes for A+ grade")
        print(f"   ")
        print(f"   OPTIONS:")
        print(f"   A. Train with current data (Grade: B-)")
        print(f"   B. Expand dataset with final_dataset.csv (Grade: A)")
    
    elif quality == "GOOD":
        print(f"   ✅ Good data! Can train decent GNN")
        print(f"   Expected grade: B+ / A-")
        print(f"   ")
        print(f"   TO IMPROVE TO A+:")
        print(f"   - Add more nodes (current: {nodes}, target: 5000+)")
        print(f"   - Use final_dataset.csv with 5904 fraud addresses")
    
    else:
        print(f"   🎉 EXCELLENT DATA! Ready for A+ GNN!")
        print(f"   Run: python scripts/train_strong_gnn.py")
    
    print(f"\n{'='*80}")

else:
    print(f"\n❌ NO GRAPH FILES FOUND!")
    print(f"   Need to build graph first")
    print(f"   Run: python scripts/build_3hop_graph.py")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
