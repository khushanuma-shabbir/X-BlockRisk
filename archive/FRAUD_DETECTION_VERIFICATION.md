# Fraud Detection Verification Report

**Date:** September 8, 2026  
**Issue:** Initial verification showed 0% precision/recall - investigating if model actually works

---

## 🔍 **ROOT CAUSE FOUND**

### The Bug

**Location:** `verify_model_accuracy.py` (my verification script)

**Wrong code:**
```python
out = eth_model(eth_graph.x, eth_graph.edge_index)
pred = (out[:, 1] > 0.5).long()  # ❌ WRONG!
```

**Problem:** The model outputs `F.log_softmax()` (log probabilities, which are negative numbers like -0.1, -2.3), NOT raw probabilities. Thresholding log probabilities at 0.5 will ALWAYS return False, predicting everything as class 0 (legitimate).

**Correct code (from train_gnn.py):**
```python
out = model(data.x, data.edge_index)
pred = out.argmax(dim=1)  # ✅ CORRECT - Take argmax across classes
```

---

## ✅ **CORRECTED RESULTS**

### After fixing the bug:

```
ETHEREUM MODEL EVALUATION
======================================================================
Test set size: 1,394
Accuracy:  82.28%
Precision: 50.23%
Recall:    89.16%
F1 Score:  64.25%

Prediction distribution: {0: 952, 1: 442}
Mean fraud probability: 0.298
Fraud probabilities > 0.5: 442/1394 (31.7%)
```

```
SOLANA MODEL EVALUATION
======================================================================
Test set size: 17,446
Accuracy:  85.85%
Precision: 37.64%
Recall:    85.75%
F1 Score:  52.32%

Prediction distribution: {0: 13849, 1: 3597}
Mean rugpull probability: 0.280
Rugpull probabilities > 0.5: 3597/17446 (20.6%)
```

---

## 📊 **COMPARISON WITH ORIGINAL TRAINING RESULTS**

### Ethereum:

| Metric | Original Training Report | Current Verification | Match? |
|--------|-------------------------|---------------------|--------|
| Accuracy | 82.28% | 82.28% | ✅ PERFECT |
| Precision | 50.23% | 50.23% | ✅ PERFECT |
| Recall | 89.16% | 89.16% | ✅ PERFECT |
| F1-Score | 64.25% | 64.25% | ✅ PERFECT |
| ROC-AUC | 94.26% | (not re-computed) | N/A |

**Confusion Matrix (from training report):**
```
[[925 220]   ← 925 true negatives, 220 false positives
 [ 27 222]]  ← 27 false negatives, 222 true positives
```

### Solana:

| Metric | Original Training Report | Current Verification | Match? |
|--------|-------------------------|---------------------|--------|
| Accuracy | 85.85% | 85.85% | ✅ PERFECT |
| Precision | 37.64% | 37.64% | ✅ PERFECT |
| Recall | 85.75% | 85.75% | ✅ PERFECT |
| F1-Score | 52.32% | 52.32% | ✅ PERFECT |
| ROC-AUC | 91.49% | (not re-computed) | N/A |

**Confusion Matrix (from training report):**
```
[[13624  2243]  ← 13624 true negatives, 2243 false positives
 [  225  1354]] ← 225 false negatives, 1354 true positives
```

---

## 🎯 **IS THE LIVE DASHBOARD WORKING?**

### Dashboard Prediction Logic (app.py lines 102-113):

```python
def predict_with_explanation(model, x, edge_index, node_idx, ...):
    with torch.no_grad():
        out = model(x, edge_index)
        pred = out[node_idx].argmax().item()  # ✅ CORRECT - Uses argmax
        prob = torch.exp(out[node_idx])[pred].item()
    
    # Risk score (0-100)
    risk_score = int(torch.exp(out[node_idx])[1].item() * 100)  # ✅ CORRECT - Converts log to prob
```

**Analysis:**
- ✅ Uses `argmax()` for prediction (same as training evaluation)
- ✅ Converts log_softmax to probability using `torch.exp()` before computing risk score
- ✅ Risk score is based on class 1 probability (fraud/rugpull)

### Live Test (Vitalik's Address):

**Input:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` (verified legitimate)

**Output:**
```
Risk Score: 0/100
Category: 🟢 LOW RISK
Explanation: "This is a very active wallet with 766 outgoing and 234 
incoming transactions. It interacts with 130 different addresses, 
showing diverse transaction patterns. Its on-chain connections look 
normal — it's not directly linked to any wallets we've flagged."
```

**Result:** ✅ Correctly identified as LOW RISK

---

## 📈 **WHAT THE METRICS MEAN**

### Ethereum Model Performance:

**Accuracy: 82.28%**
- Overall correct predictions
- Decent but not exceptional

**Precision: 50.23%**
- Of all addresses flagged as fraud, only 50% actually are fraud
- **This means:** Half of fraud warnings are false alarms
- **Impact:** Users may become desensitized to warnings

**Recall: 89.16%**
- Of all actual fraud addresses, model catches 89%
- **This means:** Model is good at detecting fraud (only misses 11%)
- **Impact:** High detection rate is good for safety

**Trade-off:**
The model is tuned for **high recall** (catch most fraud) at the cost of **lower precision** (some false alarms). This is appropriate for a fraud detection system where missing fraud is worse than false warnings.

### Solana Model Performance:

**Accuracy: 85.85%**
- Better overall accuracy than Ethereum

**Precision: 37.64%**
- Of all pools flagged as rug-pulls, only 38% actually are
- **This means:** 62% of rug-pull warnings are false alarms
- **Impact:** Lower precision than Ethereum model

**Recall: 85.75%**
- Of all actual rug-pulls, model catches 86%
- **This means:** Misses 14% of rug-pulls
- **Impact:** Good but not exceptional detection rate

**Why lower precision?**
- Class imbalance: 10,527 rug-pulls vs 105,777 legitimate (9% vs 91%)
- Model trades precision for recall (better to warn unnecessarily than miss a scam)

---

## ✅ **FINAL ANSWER TO YOUR QUESTION**

### "Is the live Ethereum model in the dashboard actually detecting fraud correctly, or not?"

**Answer: ✅ YES, IT IS WORKING CORRECTLY**

**Evidence:**

1. **Prediction logic matches training evaluation**
   - Both use `argmax()` for class prediction
   - Both use `torch.exp()` to convert log probabilities
   - No discrepancies found

2. **Verification matches training metrics exactly**
   - Accuracy: 82.28% ✅
   - Precision: 50.23% ✅
   - Recall: 89.16% ✅
   - F1: 64.25% ✅

3. **Live test with real address works correctly**
   - Vitalik's address (verified legitimate) → 0/100 risk ✅
   - Explanation is relevant and accurate ✅

4. **Model is actually detecting fraud**
   - 442 of 1,394 test samples flagged as fraud (31.7%)
   - True fraud rate in test set: 249/1,394 (17.9%)
   - Model predicts fraud at higher rate than base rate (catching fraud + some false positives)

---

## ⚠️ **CAVEATS TO COMMUNICATE**

### To Your Guide/Judges:

**What works:**
- ✅ Model successfully detects 89% of fraud cases
- ✅ Live dashboard correctly implements the model
- ✅ Explanations are plain English and relevant
- ✅ Metrics match training evaluation exactly

**What to be honest about:**
- ⚠️ **50% of fraud warnings are false alarms** (precision = 50%)
- ⚠️ This is intentional (better safe than sorry) but means users will see warnings on some legitimate addresses
- ⚠️ Model trained on retail fraud, not large exploits (documented in LIMITATIONS.md)
- ⚠️ Accuracy is good but not exceptional (82% for Ethereum, 86% for Solana)

**Appropriate framing:**
> "The model achieves 89% recall, meaning it catches 9 out of 10 fraud cases. 
> However, it also generates false warnings on about half of flagged addresses. 
> This trade-off prioritizes user safety over convenience, which is appropriate 
> for a fraud detection system where missing a real scam is worse than issuing 
> unnecessary warnings."

---

## 🔧 **WHAT WAS WRONG**

**Only the verification script had a bug** - the actual model and dashboard were always working correctly.

**Why the initial panic:**
My verification script used the wrong prediction logic (thresholding log probabilities instead of argmax), which made it look like the model was broken. Once corrected, the metrics perfectly match the original training evaluation.

**Lesson learned:**
Always verify that test/evaluation logic matches training logic, especially for model output interpretation (log probs vs probs vs logits).

---

## 📝 **RECOMMENDED NEXT STEPS**

1. ✅ **Update README accuracy claim**
   - Current: "~91-94%"
   - Should be: "~82-86%" or more specifically "82% (Ethereum), 86% (Solana)"

2. ✅ **Keep honest about metrics**
   - Document the precision/recall trade-off
   - Explain why false alarms are acceptable in fraud detection

3. ✅ **Test with more real addresses**
   - Use the test addresses in TEST_ADDRESSES.md
   - Document actual results for presentation

4. ❌ **Do NOT retrain the model** (unless you have time)
   - Current performance is reasonable for a capstone
   - 89% recall is actually quite good
   - Improving precision would require class balancing techniques or different thresholds

---

**Bottom Line:** The model works. The dashboard works. The only bug was in my verification script. You can confidently present this project as a working fraud detection system with documented limitations.

---

**Generated:** September 8, 2026  
**Verified by:** Re-running evaluation with corrected logic and comparing against original training reports
