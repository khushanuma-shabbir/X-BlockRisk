# Test Addresses for Model Validation

Real Ethereum addresses you can input into the dashboard to test if the model is working correctly.

---

## ✅ Known Legitimate Addresses (Should Show LOW RISK)

### 1. Vitalik Buterin's Wallet
```
0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```
**Expected Result:** LOW RISK (0-33/100)  
**Why:** Verified legitimate - Ethereum founder's public wallet  
**Transactions:** 700+ transactions, high volume  
**Use Case:** Test legitimate high-activity wallet

---

### 2. Uniswap V3 Router
```
0xE592427A0AEce92De3Edee1F18E0157C05861564
```
**Expected Result:** LOW RISK  
**Why:** Official Uniswap smart contract  
**Use Case:** Test legitimate smart contract detection

---

### 3. USDC Token Contract
```
0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
```
**Expected Result:** LOW RISK  
**Why:** Official stablecoin contract  
**Use Case:** Test popular token contract

---

## ⚠️ Known High-Risk/Scam Addresses

**Note:** The model is trained on retail fraud patterns. Large exploits may not be flagged correctly (see LIMITATIONS.md).

### 4. Ronin Bridge Exploiter (OUT OF TRAINING SCOPE)
```
0x098B716B8Aaf21512996dC57EB0615e2383E2f96
```
**Expected Result:** LOW RISK + High-Volume Warning ⚠️  
**Why:** Large-scale bridge hack ($625M) - outside model's training scope  
**Transactions:** 430 transactions, 182,166 ETH volume  
**Use Case:** Test out-of-scope handling & safety net warnings

---

### 5. PolyNetwork Exploiter (OUT OF TRAINING SCOPE)
```
0xC8a65Fadf0e0dDAf421F28FEAb69Bf6E2E589963
```
**Expected Result:** May show LOW RISK (large exploit, not retail fraud)  
**Why:** 2021 PolyNetwork hack ($600M+)  
**Use Case:** Test large-scale exploit handling

---

## 🧪 Test Addresses (Various Patterns)

### 6. Low-Activity Wallet
```
0x0000000000000000000000000000000000000001
```
**Expected Result:** ERROR or NO DATA  
**Why:** Burn address with minimal activity  
**Use Case:** Test error handling

---

### 7. Exchange Wallet (Binance)
```
0x28C6c06298d514Db089934071355E5743bf21d60
```
**Expected Result:** LOW RISK  
**Why:** Legitimate exchange hot wallet  
**Transactions:** Very high volume, many addresses  
**Use Case:** Test exchange wallet pattern

---

### 8. Random Active Wallet
```
0x220866B1A2219f40e72f5c628B65D54268cA3A9D
```
**Expected Result:** Varies based on actual activity  
**Use Case:** Test unknown wallet

---

## 📋 How to Test

### Step 1: Start the Dashboard
```bash
cd src
streamlit run app.py
```

### Step 2: Test Each Address
1. Copy an address from above
2. Paste into the dashboard input field
3. Click "Analyze"
4. Check if result matches expected outcome

### Step 3: Verify Results

**For Legitimate Addresses:**
- ✅ Risk Score should be LOW (0-33/100)
- ✅ Explanation should mention normal patterns
- ✅ No warnings (unless high volume)

**For Known Exploits:**
- ⚠️ May show LOW RISK (see LIMITATIONS.md)
- ✅ Should show HIGH-VOLUME WARNING for >10K ETH
- ✅ Explanation should mention pattern mismatch

**For Error Cases:**
- ✅ Should show clear error message
- ✅ Should suggest fixes
- ✅ Should not crash

---

## 🎯 Expected Behavior Summary

| Address | Type | Expected Risk | Expected Warning |
|---------|------|---------------|------------------|
| Vitalik | Legit | LOW (0-33) | None |
| Uniswap | Contract | LOW | "Smart contract" note |
| USDC | Contract | LOW | "Smart contract" note |
| Ronin | Large Exploit | LOW* | HIGH-VOLUME ⚠️ |
| PolyNetwork | Large Exploit | LOW* | May trigger HIGH-VOLUME |
| Burn Address | Minimal | ERROR/NO DATA | - |
| Binance | Exchange | LOW | May trigger HIGH-VOLUME |
| Random | Unknown | Varies | Depends on activity |

*Low risk due to training scope - see LIMITATIONS.md

---

## 📊 Test Results Template

Use this to document your testing:

```
Date: ___________
Tester: _________

Address 1 (Vitalik):
- Risk Score: ____/100
- Category: ____________
- Warning: Yes/No
- Match Expected? Yes/No

Address 2 (Ronin):
- Risk Score: ____/100
- Category: ____________
- Warning: Yes/No
- Match Expected? Yes/No

[Continue for all addresses...]

Overall Status: Pass/Fail
Notes: _______________
```

---

## 🔍 What to Check

### 1. **API Integration**
- ✅ Does it fetch real data from Etherscan?
- ✅ Shows "Live Etherscan API" badge?
- ✅ Displays actual transaction counts?

### 2. **Model Inference**
- ✅ Risk score between 0-100?
- ✅ Category matches score (LOW/MEDIUM/HIGH)?
- ✅ Confidence percentage shown?

### 3. **Explanations**
- ✅ Plain English (not technical jargon)?
- ✅ Mentions specific patterns?
- ✅ Makes sense for the address?

### 4. **Safety Nets**
- ✅ High-volume warning for >10K ETH?
- ✅ Smart contract detection working?
- ✅ Error messages clear?

### 5. **UI/UX**
- ✅ Color coding correct (green=low, red=high)?
- ✅ Technical details collapsed?
- ✅ No debug output visible?

---

## 🚨 Common Issues & Solutions

### Issue: "Could not retrieve data"
**Solution:** Check API key in `.env` file

### Issue: All addresses show 0/100
**Solution:** Model may not be loaded correctly - restart app

### Issue: "NameError" or crashes
**Solution:** Check `config/feature_columns.py` matches training data

### Issue: Slow response (>30 seconds)
**Solution:** Normal for first query (loads model), faster after

---

## 💡 Advanced Testing

### Test Edge Cases:
```
# Very new address (no history)
0x0000000000000000000000000000000000000002

# Invalid format
InvalidAddress123

# ENS domain (should work if supported)
vitalik.eth
```

---

## 📝 Quick Test Script

If you want to test programmatically:

```bash
# Quick test with Vitalik's address
python test_simple.py
```

This will:
1. Load the model
2. Fetch Vitalik's address
3. Run inference
4. Show results

---

## ✅ Success Criteria

**Your model is working correctly if:**

1. ✅ Vitalik shows LOW RISK
2. ✅ Ronin shows HIGH-VOLUME WARNING
3. ✅ Live data is fetched (not synthetic)
4. ✅ Explanations are in plain English
5. ✅ Technical details are hidden by default
6. ✅ No crashes or errors for valid addresses

---

## 📚 Additional Resources

- **More test cases:** See `test_data/README_TEST_CASES.md`
- **Model scope:** See `LIMITATIONS.md`
- **Expected behavior:** See `FINAL_VALIDATION.md`

---

**Last Updated:** September 1, 2026  
**Quick Test:** Use Vitalik's address first to verify everything works
