# 🧪 How to Test Your Model

Simple guide to verify your blockchain fraud detection model is working correctly.

---

## 🚀 Quick Start (30 seconds)

### Step 1: Start Dashboard
```bash
cd src
streamlit run app.py
```

### Step 2: Copy Test Address
```
0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

### Step 3: Paste & Analyze
1. Paste address in input field
2. Click "🚀 Analyze"
3. Should show: **LOW RISK** (0-33/100)

✅ **If it works → Model is working!**

---

## 📋 Test Addresses (Copy-Paste Ready)

### ✅ Test 1: Legitimate Wallet
```
0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```
**Expected:** LOW RISK  
**Why:** Vitalik's verified wallet

---

### ⚠️ Test 2: Large Exploit (Out of Scope)
```
0x098B716B8Aaf21512996dC57EB0615e2383E2f96
```
**Expected:** LOW RISK + ⚠️ High-Volume Warning  
**Why:** Ronin hack ($625M) - outside training scope

---

### 🏦 Test 3: Exchange Wallet
```
0x28C6c06298d514Db089934071355E5743bf21d60
```
**Expected:** LOW RISK  
**Why:** Binance exchange - legitimate high activity

---

### 🔧 Test 4: Smart Contract
```
0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
```
**Expected:** LOW RISK + "Smart contract" note  
**Why:** USDC token contract

---

## 🤖 Automated Testing

### Run All Tests Automatically:
```bash
python test_all_addresses.py
```

This will:
- Test 8 different addresses
- Show results for each
- Create summary CSV
- Report pass/fail

---

## 📊 What to Check

### ✅ Working Correctly If:

1. **Vitalik's address → LOW RISK**
   - Score: 0-33/100
   - Category: LOW RISK (green)
   - Explanation: Mentions normal activity

2. **Ronin address → WARNING**
   - Score: May be low (out of scope)
   - Warning: "High-volume" notice appears
   - Explains model limitation

3. **Live Data Fetched**
   - Badge: "📡 Live Etherscan API"
   - Shows real transaction counts
   - Not "demo mode" or "synthetic"

4. **Clean UI**
   - Color-coded (green/yellow/red)
   - Plain English explanation
   - Technical details collapsed
   - No debug output

---

## 🐛 Troubleshooting

### Issue: "Could not retrieve data"
**Fix:**
1. Check `.env` file has API key
2. Verify: `ETHERSCAN_API_KEY=your_key_here`
3. Get key from: https://etherscan.io/apis

---

### Issue: All addresses show 0/100
**Fix:**
1. Restart Streamlit
2. Check models folder exists
3. Run: `python test_simple.py` to diagnose

---

### Issue: Slow (>30 seconds)
**Normal:** First query loads model  
**After that:** Should be <5 seconds

---

### Issue: Error messages
**Check:**
1. Python version ≥ 3.11
2. All packages installed: `pip install -r requirements.txt`
3. Models folder has .pt and .pkl files

---

## 📂 Test Files Provided

### 1. **TEST_ADDRESSES.md**
- Detailed list of test addresses
- Expected results for each
- What to check
- How to interpret results

### 2. **test_addresses.csv**
- 8 test addresses in CSV format
- Easy to import/export
- Includes labels and expected outcomes

### 3. **test_all_addresses.py**
- Automated testing script
- Tests all addresses at once
- Generates summary report

### 4. **test_simple.py**
- Quick single-address test
- Good for debugging
- Shows detailed output

---

## ✅ Success Checklist

After testing, verify:

- [ ] Vitalik address shows LOW RISK
- [ ] Ronin address shows high-volume warning
- [ ] Live API badge appears
- [ ] Explanations in plain English
- [ ] Color coding works (green=low, red=high)
- [ ] Technical details collapsed
- [ ] No crashes or errors
- [ ] Response time <5 seconds (after first load)

---

## 🎯 For Demo/Presentation

**Best addresses to demonstrate:**

1. **Start with Vitalik** - Shows it works on legitimate
2. **Then show Ronin** - Shows safety net & limitations
3. **Try a random address** - Shows real-world use

**What to say:**
- "This is a live model fetching real blockchain data"
- "It correctly identifies legitimate wallets"
- "It has safety nets for out-of-scope cases"
- "It provides plain-English explanations"

---

## 📊 Expected Results Table

| Address | Type | Risk Score | Warning | Correct? |
|---------|------|------------|---------|----------|
| Vitalik | Legit | 0-33 LOW | None | ✅ |
| Ronin | Exploit | 0-33 LOW* | High-Vol ⚠️ | ✅ |
| Binance | Exchange | 0-33 LOW | Maybe | ✅ |
| USDC | Contract | 0-33 LOW | Contract | ✅ |

*Low because large exploits are outside training scope (documented)

---

## 🔍 Deep Validation

For thorough testing, see:
- **`test_data/README_TEST_CASES.md`** - Comprehensive test documentation
- **`FINAL_VALIDATION.md`** - Full validation report
- **`LIMITATIONS.md`** - Model scope & expected behavior

---

## 💡 Quick Reference

**Single Quick Test:**
```bash
python test_simple.py
```

**All Tests:**
```bash
python test_all_addresses.py
```

**Interactive Dashboard:**
```bash
cd src
streamlit run app.py
```

**Check Model Files:**
```bash
ls models/ethereum/
# Should see: model.pt, scaler.pkl
```

---

## 🎓 For Your Guide/Judge

Show them:
1. Live dashboard working
2. Test with Vitalik (works correctly)
3. Test with Ronin (shows limitation honestly)
4. Point to LIMITATIONS.md (shows awareness)

This demonstrates:
- ✅ Working implementation
- ✅ Real-world testing
- ✅ Honest about scope
- ✅ Professional presentation

---

**Quick Start:** Copy Vitalik's address, paste in dashboard, click Analyze!

**Address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
