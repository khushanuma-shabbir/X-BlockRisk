# Recommended Test Addresses for Validation

Use these addresses to validate that the fraud detection pipeline is working correctly.

## ✅ Known Legitimate Ethereum Addresses (Should score < 33)

### 1. Vitalik Buterin
**Address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`  
**Description:** Ethereum co-founder's public address  
**Expected Score:** 0-10/100 (Very Low Risk)  
**Why:** High activity, transparent, well-known legitimate entity

### 2. Ethereum Foundation
**Address:** `0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe`  
**Description:** Ethereum Foundation official address  
**Expected Score:** 0-15/100 (Very Low Risk)  
**Why:** Official foundation address with transparent operations

### 3. Uniswap V2 Router
**Address:** `0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D`  
**Description:** Uniswap V2 Router contract  
**Expected Score:** 0-20/100 (Low Risk)  
**Why:** Well-established DeFi protocol, audited smart contract

### 4. Binance Hot Wallet
**Address:** `0xF977814e90dA44bFA03b6295A0616a897441aceC`  
**Description:** Binance exchange hot wallet  
**Expected Score:** 0-25/100 (Low Risk)  
**Why:** Major centralized exchange, high volume legitimate operations

---

## 🚨 Known Fraud/Scam Addresses (Should score > 66)

**⚠️ YOU NEED TO PROVIDE THESE ⚠️**

To complete validation, you'll need to add **3 known fraud/scam addresses** that you have verified. These could be:

### Sources for Fraud Addresses:
1. **Etherscan Phishing Database:** https://etherscan.io/accounts/label/phish-hack
2. **ChainAbuse:** https://www.chainabuse.com/
3. **Scam Sniffer Reports:** https://scamsniffer.io/
4. **Your own documented fraud cases**

### What to Look For:
- Addresses involved in rug pulls
- Confirmed phishing addresses
- Smart contract exploits
- Ponzi schemes
- Token scams

### Example Format:
```python
("0xSCAM_ADDRESS_HERE", "Brief description of the scam"),
```

---

## 🧪 How to Test

### Method 1: Using the Validation Script

1. Open `validate_fix.py`
2. Find the `test_cases` list
3. Add your fraud addresses:
   ```python
   test_cases = [
       # FRAUD addresses
       ("0xYOUR_FRAUD_ADDRESS_1", "Rug Pull - Project XYZ"),
       ("0xYOUR_FRAUD_ADDRESS_2", "Phishing Scam - Fake Airdrop"),
       ("0xYOUR_FRAUD_ADDRESS_3", "Exit Scam - DEX Project"),
       
       # LEGITIMATE addresses (already included)
       ("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "Vitalik Buterin"),
       ("0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe", "Ethereum Foundation"),
   ]
   ```
4. Run: `python validate_fix.py`
5. Verify results match expectations

### Method 2: Using the Dashboard

1. Start dashboard: `streamlit run src/app.py`
2. Paste each address one by one
3. Record the risk scores
4. Compare with expectations

---

## 📊 Expected Results

### Validation Criteria

| Category | Expected Score | What It Means |
|----------|----------------|---------------|
| **Known Fraud** | 66-100 | High Risk - Model correctly identifies fraud patterns |
| **Known Legitimate** | 0-33 | Low Risk - Model correctly identifies normal activity |
| **Uncertain** | 33-66 | Medium Risk - Ambiguous patterns |

### Success Criteria

For the fix to be considered fully validated:

1. ✅ At least 2/3 legitimate addresses score < 33
2. ✅ At least 2/3 fraud addresses score > 66
3. ✅ No more than 1 address scores at extremes (0 or 100) due to edge cases

---

## ⚠️ Important Notes

### About Legitimate Addresses:
- **Very new addresses** (< 10 transactions) may score higher due to lack of data
- **Inactive addresses** (no transactions in 6+ months) may show unusual scores
- **Exchange addresses** with extreme volumes may be clipped and show lower scores

### About Fraud Addresses:
- **Old scams** (> 2 years ago) may have different patterns than modern fraud
- **Sophisticated scams** that mimic legitimate patterns may score lower
- **One-time scams** with minimal activity may not have enough data

### Model Limitations:
- The model is trained on historical fraud patterns
- New attack vectors may not be recognized
- Edge cases with extreme activity levels may be affected by feature clipping

---

## 🔍 Debugging Failed Validations

### If a legitimate address scores HIGH (> 66):

1. **Check transaction patterns:**
   - Is it an exchange/mixer with unusual patterns?
   - Does it interact with many unique addresses rapidly?
   - Are there large value transfers in short time periods?

2. **Run debug script:**
   ```bash
   python test_fraud_detection_debug.py
   ```
   - Look for extreme feature values
   - Check if features are being clipped
   - Verify K-NN neighbor distances are reasonable (< 100)

3. **Possible causes:**
   - Address has patterns similar to training fraud data
   - Features are still extreme despite clipping
   - Model was not trained on similar legitimate patterns

### If a fraud address scores LOW (< 33):

1. **Check fraud type:**
   - Is it a sophisticated scam that mimics normal behavior?
   - Does it have minimal transaction history?
   - Is it an old fraud with outdated patterns?

2. **Review transaction data:**
   - Look at transaction count, volumes, and timing
   - Compare with training data patterns

3. **Possible causes:**
   - Fraud pattern is too new/sophisticated for model
   - Insufficient transaction data for classification
   - Fraud type not represented in training data

---

## 📝 Reporting Results

When reporting validation results, please include:

1. **Address and label** for each test case
2. **Risk score** produced by the model
3. **Expected vs Actual** comparison
4. **Any unusual patterns** observed
5. **Screenshots** from the dashboard (optional)

### Example Report:
```
Validation Results:

LEGITIMATE ADDRESSES:
✅ Vitalik (0xd8dA...6045): 0/100 - PASS (expected < 33)
✅ Ethereum Foundation (0xde0B...7BAe): 12/100 - PASS (expected < 33)

FRAUD ADDRESSES:
✅ Rug Pull ABC (0x1234...5678): 87/100 - PASS (expected > 66)
❌ Phishing XYZ (0x9abc...def0): 45/100 - FAIL (expected > 66)
   -> Need to investigate why this scored medium risk

OVERALL: 3/4 passed validation (75%)
```

---

## 🚀 Ready to Validate

1. **Add your fraud addresses** to `validate_fix.py`
2. **Run validation:** `python validate_fix.py`
3. **Review results** and compare with expectations
4. **Report any unexpected results** for further investigation

---

**Need more help?** Check `docs/BUG_FIX_REPORT.md` for detailed technical information.
