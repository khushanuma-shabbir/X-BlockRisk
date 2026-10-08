# Fraud Detection System - Performance Metrics

## Test Dataset

- Total addresses tested: 13
- Fraud addresses: 5
- Legitimate addresses: 8

## Confusion Matrix

```
                 Predicted
                 Legit    Fraud
Actual  Legit      8        0
        Fraud      4        1
```

## Performance Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Accuracy** | **69.23%** | Overall correctness |
| **Precision** | **100.00%** | Accuracy of fraud predictions |
| **Recall** | **20.00%** | Coverage of actual fraud |
| **F1 Score** | **0.3333** | Balanced performance measure |

## Detailed Results

| # | Address | Actual | Predicted | Score | Correct |
|---|---------|--------|-----------|-------|----------|
| 1 | Fake Phishing | FRAUD | FRAUD | 70.0 | ✅ |
| 2 | Giveaway Scam | FRAUD | LEGIT | 0.4 | ❌ |
| 3 | Fake Site Phishing | FRAUD | LEGIT | 12.4 | ❌ |
| 4 | Phishing | FRAUD | LEGIT | 30.4 | ❌ |
| 5 | Phishing | FRAUD | LEGIT | 0.4 | ❌ |
| 6 | USDT Contract | LEGIT | LEGIT | 9.5 | ✅ |
| 7 | USDC Contract | LEGIT | LEGIT | 6.4 | ✅ |
| 8 | WETH Contract | LEGIT | LEGIT | 7.7 | ✅ |
| 9 | Vitalik.eth | LEGIT | LEGIT | 15.4 | ✅ |
| 10 | Uniswap V2 Router | LEGIT | LEGIT | 6.4 | ✅ |
| 11 | Binance 14 | LEGIT | LEGIT | 24.4 | ✅ |
| 12 | Binance 15 | LEGIT | LEGIT | 30.4 | ✅ |
| 13 | ETH2 Deposit Contract | LEGIT | LEGIT | 6.4 | ✅ |

## Grade: C or below (Needs Improvement)

**Overall System Performance: 69.23% Accuracy, 0.3333 F1 Score**
