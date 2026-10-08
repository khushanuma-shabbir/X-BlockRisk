"""Quick metrics calculation - no Unicode output"""
import sys
import os

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.live.fetch_ethereum import fetch_ethereum_wallet
from src.detection.hybrid_detector import HybridDetector

# Test addresses
test_addresses = {
    'fraud': [
        ('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', 'Fake Phishing'),
        ('0x1da5821544e25c636c1417ba96ade4cf6d2f9b5a', 'Giveaway Scam'),
        ('0xd882cfc20f52f2599d84b8e8d58c7fb62cfe344b', 'Fake Site Phishing'),
        ('0x0681d8Db095565FE8A346fA0277bFfdE9C0EDdBf', 'Phishing'),
        ('0xC61b9BB3A7a0767E3179713f3A5C7a9aedCE193C', 'Phishing'),
    ],
    'legitimate': [
        ('0xdAC17F958D2ee523a2206206994597C13d831ec7', 'USDT Contract'),
        ('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'USDC Contract'),
        ('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'WETH Contract'),
        ('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 'Vitalik.eth'),
        ('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', 'Uniswap V2 Router'),
        ('0x28C6c06298d514Db089934071355E5743bf21d60', 'Binance 14'),
        ('0x21a31Ee1aFc51d94C2eFccaA2092aD1028285549', 'Binance 15'),
        ('0x00000000219ab540356cBB839Cbe05303d7705Fa', 'ETH2 Deposit Contract'),
    ]
}

# Initialize detector
detector = HybridDetector()

# Results
results = []
TP = TN = FP = FN = 0

print("\nTesting fraud addresses...")
for addr, name in test_addresses['fraud']:
    try:
        features_dict, is_contract, errors, source_code = fetch_ethereum_wallet(addr, "test", "0.0.0.0")
        if features_dict:
            final_score, category, explanations = detector.detect(addr, features_dict, 15.0)
            predicted = 1 if final_score >= 30 else 0
            if predicted == 1:
                TP += 1
                print(f"  [OK] {name}: {final_score:.1f}/100 - FRAUD (Caught)")
            else:
                FN += 1
                print(f"  [MISS] {name}: {final_score:.1f}/100 - LEGIT (Missed)")
    except Exception as e:
        print(f"  [ERROR] {name}: {str(e)[:50]}")

print("\nTesting legitimate addresses...")
for addr, name in test_addresses['legitimate']:
    try:
        features_dict, is_contract, errors, source_code = fetch_ethereum_wallet(addr, "test", "0.0.0.0")
        if features_dict:
            final_score, category, explanations = detector.detect(addr, features_dict, 15.0)
            predicted = 1 if final_score >= 30 else 0
            if predicted == 0:
                TN += 1
                print(f"  [OK] {name}: {final_score:.1f}/100 - LEGIT (Correct)")
            else:
                FP += 1
                print(f"  [FALSE ALARM] {name}: {final_score:.1f}/100 - FRAUD (Wrong!)")
    except Exception as e:
        print(f"  [ERROR] {name}: {str(e)[:50]}")

# Calculate metrics
total = TP + TN + FP + FN
accuracy = (TP + TN) / total * 100 if total > 0 else 0
precision = TP / (TP + FP) * 100 if (TP + FP) > 0 else 0
recall = TP / (TP + FN) * 100 if (TP + FN) > 0 else 0
f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

print("\n" + "="*60)
print("RESULTS (Threshold = 30)")
print("="*60)
print(f"True Positives (TP):  {TP} - Correctly caught fraud")
print(f"True Negatives (TN):  {TN} - Correctly identified legit")
print(f"False Positives (FP): {FP} - Falsely flagged legit as fraud")
print(f"False Negatives (FN): {FN} - Missed fraud")
print("-"*60)
print(f"Accuracy:  {accuracy:.2f}%")
print(f"Precision: {precision:.2f}%")
print(f"Recall:    {recall:.2f}%")
print(f"F1 Score:  {f1/100:.4f}")
print("="*60)

if FP == 0:
    print("\n[SUCCESS] ZERO FALSE POSITIVES! Perfect precision.")
if recall > 20:
    print(f"\n[IMPROVEMENT] Recall improved from 20% to {recall:.0f}%!")
