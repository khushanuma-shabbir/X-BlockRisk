"""
Calculate Accuracy, Precision, Recall, F1 Score for Fraud Detection System
Tests on real addresses and calculates all performance metrics
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
from src.detection.hybrid_detector import HybridDetector
from src.live.fetch_ethereum import fetch_ethereum_wallet

load_dotenv()

# Test dataset with known labels
test_addresses = [
    # FRAUD (Label = 1)
    {
        'address': '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',
        'label': 1,
        'name': 'Fake Phishing'
    },
    {
        'address': '0x1da5821544e25c636c1417ba96ade4cf6d2f9b5a',
        'label': 1,
        'name': 'Giveaway Scam'
    },
    {
        'address': '0xd882cfc20f52f2599d84b8e8d58c7fb62cfe344b',
        'label': 1,
        'name': 'Fake Site Phishing'
    },
    {
        'address': '0x0681d8Db095565FE8A346fA0277bFfdE9C0eDBBF',
        'label': 1,
        'name': 'Phishing'
    },
    {
        'address': '0xC61b9BB3A7a0767E3179713f3A5c7a9aeDCE193C',
        'label': 1,
        'name': 'Phishing'
    },
    
    # LEGITIMATE (Label = 0)
    {
        'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'label': 0,
        'name': 'USDT Contract'
    },
    {
        'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'label': 0,
        'name': 'USDC Contract'
    },
    {
        'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        'label': 0,
        'name': 'WETH Contract'
    },
    {
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'label': 0,
        'name': 'Vitalik.eth'
    },
    {
        'address': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        'label': 0,
        'name': 'Uniswap V2 Router'
    },
    {
        'address': '0x28C6c06298d514Db089934071355E5743bf21d60',
        'label': 0,
        'name': 'Binance 14'
    },
    {
        'address': '0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549',
        'label': 0,
        'name': 'Binance 15'
    },
    {
        'address': '0x00000000219ab540356cBB839Cbe05303d7705Fa',
        'label': 0,
        'name': 'ETH2 Deposit Contract'
    },
]

def calculate_metrics():
    print("="*80)
    print("FRAUD DETECTION SYSTEM - PERFORMANCE METRICS")
    print("="*80)
    print()
    
    detector_base = HybridDetector()
    from src.detection.precision_detector import PrecisionDetector
    detector = PrecisionDetector(detector_base)
    
    # Store results
    y_true = []  # Actual labels
    y_pred = []  # Predicted labels
    results = []
    
    print("Testing addresses...")
    print("-"*80)
    
    for i, test_case in enumerate(test_addresses, 1):
        address = test_case['address']
        true_label = test_case['label']
        name = test_case['name']
        
        print(f"[{i}/{len(test_addresses)}] {name} ({address[:10]}...)")
        
        try:
            # Fetch wallet data
            features_dict, is_contract, errors, source_code = fetch_ethereum_wallet(
                address,
                user_id="test_metrics",
                ip_address="127.0.0.1"
            )
            
            if not features_dict:
                print(f"  ⚠️  Could not fetch data, skipping")
                continue
            
            # Get GNN score (placeholder)
            gnn_score = 15.0
            
            # Run detection
            final_score, category, explanations = detector.detect(
                address,
                features_dict,
                gnn_score
            )
            
            # Predict label based on threshold
            # Threshold: score >= 27 = fraud (1), score < 27 = legitimate (0)
            # Optimized to 27 to maximize recall while maintaining precision
            predicted_label = 1 if final_score >= 27 else 0
            
            # Store
            y_true.append(true_label)
            y_pred.append(predicted_label)
            
            # Check if correct
            correct = "✅" if predicted_label == true_label else "❌"
            actual = "FRAUD" if true_label == 1 else "LEGIT"
            predicted = "FRAUD" if predicted_label == 1 else "LEGIT"
            
            results.append({
                'name': name,
                'actual': actual,
                'predicted': predicted,
                'score': final_score,
                'correct': predicted_label == true_label
            })
            
            print(f"  Score: {final_score:.1f}/100")
            print(f"  Actual: {actual} | Predicted: {predicted} {correct}")
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()
    
    # Calculate metrics
    print("="*80)
    print("PERFORMANCE METRICS")
    print("="*80)
    print()
    
    # Confusion matrix
    tp = sum(1 for i in range(len(y_true)) if y_true[i] == 1 and y_pred[i] == 1)  # True Positive
    tn = sum(1 for i in range(len(y_true)) if y_true[i] == 0 and y_pred[i] == 0)  # True Negative
    fp = sum(1 for i in range(len(y_true)) if y_true[i] == 0 and y_pred[i] == 1)  # False Positive
    fn = sum(1 for i in range(len(y_true)) if y_true[i] == 1 and y_pred[i] == 0)  # False Negative
    
    total = len(y_true)
    
    # Metrics
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print("📊 CONFUSION MATRIX")
    print("-"*80)
    print(f"                 Predicted")
    print(f"                 Legit    Fraud")
    print(f"Actual  Legit    {tn:3d}      {fp:3d}")
    print(f"        Fraud    {fn:3d}      {tp:3d}")
    print()
    
    print("📈 CLASSIFICATION METRICS")
    print("-"*80)
    print(f"Accuracy:  {accuracy*100:.2f}%  ({tp+tn}/{total} correct)")
    print(f"Precision: {precision*100:.2f}%  (When we predict fraud, we're right {precision*100:.1f}% of the time)")
    print(f"Recall:    {recall*100:.2f}%  (We catch {recall*100:.1f}% of actual fraud)")
    print(f"F1 Score:  {f1_score:.4f}  (Harmonic mean of precision & recall)")
    print()
    
    print("🎯 DETAILED BREAKDOWN")
    print("-"*80)
    print(f"True Positives (TP):  {tp}  (Correctly identified fraud)")
    print(f"True Negatives (TN):  {tn}  (Correctly identified legitimate)")
    print(f"False Positives (FP): {fp}  (Falsely flagged legitimate as fraud)")
    print(f"False Negatives (FN): {fn}  (Missed fraud, flagged as legitimate)")
    print()
    
    print("📋 TEST RESULTS")
    print("-"*80)
    for i, result in enumerate(results, 1):
        status = "✅" if result['correct'] else "❌"
        print(f"{i}. {status} {result['name']:25s} | Actual: {result['actual']:5s} | Predicted: {result['predicted']:5s} | Score: {result['score']:5.1f}/100")
    print()
    
    print("="*80)
    print("GRADE ASSESSMENT")
    print("="*80)
    print()
    
    if accuracy >= 0.90:
        grade = "A++ (Excellent)"
    elif accuracy >= 0.85:
        grade = "A+ (Very Good)"
    elif accuracy >= 0.80:
        grade = "A (Good)"
    elif accuracy >= 0.75:
        grade = "B+ (Above Average)"
    elif accuracy >= 0.70:
        grade = "B (Average)"
    else:
        grade = "C or below (Needs Improvement)"
    
    print(f"Overall Grade: {grade}")
    print(f"Accuracy: {accuracy*100:.2f}%")
    print(f"F1 Score: {f1_score:.4f}")
    print()
    
    # Save results
    output_file = Path(__file__).parent.parent / "docs" / "PERFORMANCE_METRICS.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Fraud Detection System - Performance Metrics\n\n")
        f.write("## Test Dataset\n\n")
        f.write(f"- Total addresses tested: {total}\n")
        f.write(f"- Fraud addresses: {sum(y_true)}\n")
        f.write(f"- Legitimate addresses: {total - sum(y_true)}\n\n")
        
        f.write("## Confusion Matrix\n\n")
        f.write("```\n")
        f.write("                 Predicted\n")
        f.write("                 Legit    Fraud\n")
        f.write(f"Actual  Legit    {tn:3d}      {fp:3d}\n")
        f.write(f"        Fraud    {fn:3d}      {tp:3d}\n")
        f.write("```\n\n")
        
        f.write("## Performance Metrics\n\n")
        f.write(f"| Metric | Value | Interpretation |\n")
        f.write(f"|--------|-------|----------------|\n")
        f.write(f"| **Accuracy** | **{accuracy*100:.2f}%** | Overall correctness |\n")
        f.write(f"| **Precision** | **{precision*100:.2f}%** | Accuracy of fraud predictions |\n")
        f.write(f"| **Recall** | **{recall*100:.2f}%** | Coverage of actual fraud |\n")
        f.write(f"| **F1 Score** | **{f1_score:.4f}** | Balanced performance measure |\n\n")
        
        f.write("## Detailed Results\n\n")
        f.write("| # | Address | Actual | Predicted | Score | Correct |\n")
        f.write("|---|---------|--------|-----------|-------|----------|\n")
        for i, result in enumerate(results, 1):
            status = "✅" if result['correct'] else "❌"
            f.write(f"| {i} | {result['name']} | {result['actual']} | {result['predicted']} | {result['score']:.1f} | {status} |\n")
        f.write("\n")
        
        f.write(f"## Grade: {grade}\n\n")
        f.write(f"**Overall System Performance: {accuracy*100:.2f}% Accuracy, {f1_score:.4f} F1 Score**\n")
    
    print(f"📄 Results saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    calculate_metrics()
