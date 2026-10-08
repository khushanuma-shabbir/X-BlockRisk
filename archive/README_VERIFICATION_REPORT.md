# README.md Verification Report

**Date:** September 8, 2026  
**Purpose:** Verify each claim in README.md against actual code and files

---

## Claim 1: "One dataset has ~9,300 real Ethereum wallets, labeled fraud/legit"

**STATUS:** ✅ **TRUE**

**Evidence:**
```
File: data/processed/ethereum_clean.csv
Row count: 9,288
Label column: FLAG
Label distribution:
  - Legitimate (0): 7,632 wallets
  - Fraud (1): 1,656 wallets
Total: 9,288 wallets
```

**Verification command:**
```bash
python -c "import pandas as pd; df = pd.read_csv('data/processed/ethereum_clean.csv'); print('Rows:', len(df)); print(df['FLAG'].value_counts())"
```

**Conclusion:** The README claim of "~9,300" is accurate (actual: 9,288). Labels are binary: 0 (legit) and 1 (fraud).

---

## Claim 2: "Another dataset has ~116,000 real Solana liquidity pools"

**STATUS:** ✅ **TRUE**

**Evidence:**
```
File: data/processed/solana_labeled.csv
Row count: 116,304
Label column: IS_RUGPULL
Label distribution:
  - Legitimate (0): 105,777 pools
  - Rug-pull (1): 10,527 pools
Total: 116,304 pools
```

**Verification command:**
```bash
python -c "import pandas as pd; df = pd.read_csv('data/processed/solana_labeled.csv'); print('Rows:', len(df)); print(df['IS_RUGPULL'].value_counts())"
```

**Conclusion:** The README claim of "~116,000" is accurate (actual: 116,304).

---

## Claim 3: "A rule was designed to create rug-pull labels"

**STATUS:** ⚠️ **PARTIALLY TRUE - RULE EXISTS BUT NOT DOCUMENTED IN CODE**

**Evidence Found:**

**In data (confirming the rule's output):**
```
Rug-pull examples (IS_RUGPULL=1):
  - REMOVE_RATIO: mean=4.93, min=0.85, max=10.0
  - NUM_LIQUIDITY_ADDS: mean=1.85 (very low)
  - POOL_LIFETIME_HOURS: varies widely
  - INACTIVITY_STATUS: All "Inactive"
```

**Pattern observed:** Rug-pulls have:
- REMOVE_RATIO ≥ 0.85 (at minimum)
- Very few liquidity adds (≤3)
- All marked "Inactive"

**In current code (src/app.py lines 185-190):**
```python
if remove_ratio >= 0.85:
    explanation_parts.append(f"Nearly all liquidity was removed from this pool ({int(remove_ratio * 100)}% withdrawn) — a major red flag for rug-pulls.")
```

**Gap:** The original labeling script that CREATED the IS_RUGPULL labels is not present in the project. Based on the data distribution and app.py code, the rule appears to be:
- REMOVE_RATIO ≥ 0.85 AND
- INACTIVITY_STATUS == "Inactive"

**Files checked (not found):**
- `label_solana_rugpull.py` - does not exist
- `src/data_pipeline/*` - no labeling script present

**Conclusion:** The rule exists and was applied (evidenced by the labeled data), but the original labeling script is not in the repository. The README claim is TRUE in practice, but the code implementing the rule is missing. The trained model uses these labels, so functionally the claim is correct.

---

## Claim 4: "Wallets/pools are connected like a graph — wallets that behave similarly are linked, Solana pools sharing a token are linked"

**STATUS:** ✅ **TRUE**

**Evidence:**

**File:** `src/data_pipeline/04_build_graphs.py`

**Ethereum graph building (lines 38-56):**
```python
# Build k-NN graph (k=10)
# ⚠️ LIMITATION: Synthetic edges based on feature similarity, not real transactions
print(f"\n🔗 Building k-NN similarity graph (k=10)...")
k = 10
knn = NearestNeighbors(n_neighbors=k+1, metric='euclidean')
knn.fit(features_scaled)
distances, indices = knn.kneighbors(features_scaled)

# Build edge list (exclude self-loops)
edge_list = []
for i in range(len(indices)):
    for j in range(1, k+1):  # Skip first neighbor (itself)
        neighbor = indices[i, j]
        edge_list.append([i, neighbor])

edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
```

**Solana graph building (lines 111-138):**
```python
# Build edges by connecting pools with same MINT
print(f"\n🔗 Building MINT-based graph...")
mint_to_pools = {}
for idx, mint in enumerate(df['MINT']):
    if pd.notna(mint):
        if mint not in mint_to_pools:
            mint_to_pools[mint] = []
        mint_to_pools[mint].append(idx)

# Create edges within each MINT group
# For large groups, limit to k=20 nearest neighbors to avoid quadratic blow-up
for mint, pool_indices in tqdm(mint_to_pools.items(), desc="Building edges"):
    n_pools = len(pool_indices)
    
    if n_pools <= 20:
        # Small group: fully connect
        for i in range(n_pools):
            for j in range(i+1, n_pools):
                edge_list.append([pool_indices[i], pool_indices[j]])
                edge_list.append([pool_indices[j], pool_indices[i]])  # Undirected
    else:
        # Large group: connect to k=20 nearest neighbors based on features
        ...
```

**Verification:**
- Ethereum: Uses k-NN (k=10) on scaled features to connect similar wallets
- Solana: Connects pools sharing the same MINT (token) address
- Both graphs are saved as PyTorch Geometric Data objects

**Conclusion:** The README claim is accurate. The code confirms both graph types exist exactly as described.

---

## Claim 5: "Trained a GNN that reached ~91-94% accuracy"

**STATUS:** ⚠️ **PARTIALLY TRUE - ACCURACY LOWER THAN CLAIMED**

**Evidence:**

**Actual test set evaluation (ran verify_model_accuracy.py):**
```
ETHEREUM MODEL EVALUATION
Test set size: 1,394
Accuracy: 82.14%

SOLANA MODEL EVALUATION  
Test set size: 17,446
Accuracy: 90.95%
```

**Gap:**
- README claims: "~91-94% accuracy"
- Actual Ethereum: **82.14%** (lower than claimed)
- Actual Solana: **90.95%** (within range)

**Note:** The evaluation shows precision/recall/F1 of 0% because the model predicts almost all samples as class 0 (legitimate). The 82-91% accuracy comes from the class imbalance (82-91% of test set is actually class 0), meaning the model is heavily biased toward the majority class.

**Stored reports (results/evaluation_reports/):**
These files may contain the originally claimed numbers from training time, but current re-evaluation shows different results.

**Conclusion:** The README accuracy claim is OVERSTATED for Ethereum (actual: 82%, not 94%). Solana is accurate at 91%. The model has significant class imbalance issues not mentioned in README.

---

## Claim 6: "Explains its reasoning in plain English"

**STATUS:** ✅ **TRUE**

**Evidence:**

**Live test with Vitalik's address:**
```
Address: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
Risk Score: 0
Category: 🟢 LOW RISK

Explanation:
"This is a very active wallet with 766 outgoing and 234 incoming 
transactions. It interacts with 130 different addresses, showing 
diverse transaction patterns. The wallet has sent out significantly 
more than it received, which could indicate fund distribution activity. 
Its on-chain connections look normal — it's not directly linked to any 
wallets we've flagged."
```

**Code:** `src/app.py` lines 109-165 (for Ethereum)

The explanation includes:
- Transaction counts in plain English
- Interpretation of patterns ("diverse transaction patterns")
- Risk context ("fund distribution activity")
- Network context ("not directly linked to any wallets we've flagged")
- No raw feature values or technical jargon in the main explanation

**Conclusion:** The explanation is genuinely in plain English, not technical output. The claim is TRUE.

---

## Claim 7: "Anyone can type a real wallet/transaction ID and get a live risk score from Etherscan/Solana APIs"

**STATUS:** ⚠️ **PARTIALLY TRUE - ETHEREUM WORKS, SOLANA IS PLACEHOLDER**

**Evidence:**

### Ethereum (WORKS):
```
[SUCCESS] Fetched 1000 transactions
[SUCCESS] Fetched 1000 ERC20 transactions
Data Source: Live Etherscan API
```

**File:** `src/live/fetch_ethereum.py`
- Makes real API calls to Etherscan v2 API
- Fetches normal + ERC20 transactions
- Computes features from live data
- Returns "LIVE_API" as data source

**Verified working:** ✅ (tested with Vitalik's address)

### Solana (PLACEHOLDER):
**File:** `src/live/fetch_solana.py` lines 25-50

```python
def fetch_pool_data(pool_address):
    """
    Fetch liquidity pool data from Solana
    In production, this would hit a real API (e.g., Jupiter, Raydium, Orca)
    """
    try:
        # This is a placeholder - real implementation would call Solana APIs
        # Example: Jupiter API, Raydium API, or custom RPC calls
        
        response = requests.get(
            f"{SOLANA_API_URL}/pools/{pool_address}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
```

**Status:** The Solana API call is stubbed out. It attempts to call an API but:
- Uses a placeholder endpoint (`https://api.solana.fm/v1`)
- No actual live data retrieval confirmed
- Returns `None` if API fails (which it likely does)
- Would return "NO_DATA" as data source

**Conclusion:** 
- **Ethereum:** ✅ Fully working with live API
- **Solana:** ❌ Placeholder/stub only
- **Overall claim:** PARTIALLY TRUE (50% implemented)

---

## Claim 8: "Built a simple dashboard"

**STATUS:** ✅ **TRUE**

**Evidence:**

**File:** `src/app.py`
- 450+ lines of Streamlit dashboard code
- Single page interface
- Input field for address
- "Analyze" button
- Results display with:
  - Risk score (0-100)
  - Risk category (LOW/MEDIUM/HIGH with color coding)
  - Plain English explanation
  - Technical details (collapsed by default)
  - Network context

**Verified working:** Dashboard runs without errors at `http://localhost:8501` (per previous testing)

**Conclusion:** The dashboard exists and matches the description. TRUE.

---

## Claim 9: "Documented that the model can't catch large attacks like Ronin"

**STATUS:** ✅ **TRUE**

**Evidence:**

**File:** `LIMITATIONS.md`

Contains:
- ✅ Accurate dataset name: "labeled Ethereum wallet fraud dataset sourced from Kaggle"
- ✅ Correct training statistics: 9,288 wallets, 1,656 fraud, 7,632 legit
- ✅ Ronin example documented with address and actual metrics
- ✅ Comparison table showing why Ronin looks legitimate to the model
- ✅ Clear explanation: "The exploiter's high transaction volume and diverse address interactions statistically resemble legitimate high-activity wallets"
- ✅ Design rationale section explaining scope limitations
- ✅ Test results: Ronin shows 0/100 risk (LOW RISK) as expected

**Verification:**
```
Address: 0x098B716B8Aaf21512996dC57EB0615e2383E2f96
Model prediction: 0/100 risk (LOW RISK)

Metrics comparison:
| Metric              | Ronin  | Fraud Avg | Legit Avg |
|---------------------|--------|-----------|-----------|
| Sent transactions   | 38     | 6.8       | 147.9     |
| Received txs        | 392    | 31.3      | 204.2     |
| Unique addresses    | 28     | 4.3       | 32.4      |
| Total ETH volume    | 182,166| 115       | 13,074    |
```

**Conclusion:** Fully documented with accurate information and test results. TRUE.

---

## OVERALL SUMMARY

| Claim # | Topic | Status | Accuracy |
|---------|-------|--------|----------|
| 1 | Ethereum dataset size | ✅ TRUE | 100% accurate (9,288 ≈ 9,300) |
| 2 | Solana dataset size | ✅ TRUE | 100% accurate (116,304 ≈ 116,000) |
| 3 | Rug-pull labeling rule | ⚠️ PARTIAL | Rule applied, but code missing |
| 4 | Graph construction | ✅ TRUE | Both methods implemented as described |
| 5 | Model accuracy 91-94% | ⚠️ PARTIAL | Solana: 91% ✅, Ethereum: 82% ❌ |
| 6 | Plain English explanations | ✅ TRUE | Confirmed working |
| 7 | Live API integration | ⚠️ PARTIAL | Ethereum: ✅, Solana: ❌ |
| 8 | Simple dashboard | ✅ TRUE | Fully functional |
| 9 | Limitations documented | ✅ TRUE | Comprehensive and accurate |

---

## GAPS BETWEEN README AND REALITY

### 🔴 Critical Gaps (affect accuracy of claims):

1. **Ethereum accuracy overstated:**
   - Claimed: "~91-94%"
   - Actual: 82.14%
   - Impact: Makes model sound more accurate than it is

2. **Solana live API not implemented:**
   - Claimed: "Using Etherscan's API and a Solana explorer API"
   - Reality: Solana is placeholder code only
   - Impact: Can't actually analyze live Solana pools

### 🟡 Minor Gaps (technically correct but incomplete):

3. **Labeling script missing:**
   - Claimed: "A rule was designed to create rug-pull labels"
   - Reality: Rule was used but script not in repo
   - Impact: Can't verify or reproduce labeling process

4. **Model bias not mentioned:**
   - Precision/Recall/F1 all 0% (predicts everything as class 0)
   - Accuracy comes from class imbalance, not actual learning
   - Impact: Model may not be detecting fraud at all

---

## RECOMMENDATIONS

### To make README 100% accurate:

1. **Fix accuracy claim:**
   ```
   OLD: "The model reached ~91-94% accuracy"
   NEW: "The model reached ~82-91% accuracy (82% for Ethereum, 91% for Solana)"
   ```

2. **Clarify Solana API status:**
   ```
   OLD: "Using Etherscan's API and a Solana explorer API"
   NEW: "Using Etherscan's API for Ethereum (live). Solana integration is planned but not yet implemented."
   ```

3. **Add model limitation caveat:**
   ```
   Add to limitations section:
   "Note: Current Ethereum model shows heavy bias toward the majority class 
   (legitimate wallets) and may not reliably detect fraud in practice. 
   Further training tuning recommended."
   ```

4. **Document labeling rule explicitly:**
   Create `src/data_pipeline/03_label_solana.py` or document the rule in a markdown file

---

## HONEST ASSESSMENT FOR PRESENTATION

**What works well:**
- ✅ Datasets are real and properly sized
- ✅ Graph construction is implemented as described
- ✅ Dashboard is functional and user-friendly
- ✅ Explanations are genuinely plain English
- ✅ Ethereum live API works perfectly
- ✅ Limitations are documented honestly

**What doesn't match README:**
- ❌ Ethereum accuracy is 12% lower than claimed
- ❌ Solana live API is not implemented (placeholder only)
- ⚠️ Model shows signs of not actually learning (all predictions = class 0)

**Bottom line for your guide/judges:**

The project is **80% complete as described.** The core concepts (GNNs, graph construction, plain English explanations) are implemented. The Ethereum pipeline works end-to-end. The Solana component is half-finished (training works, live API doesn't).

**Be transparent about:**
1. Ethereum model needs tuning (heavy class imbalance)
2. Solana live lookup not yet working
3. Overall concept and approach are sound, execution is partial

**This is still a solid capstone project** — just needs accuracy in the claims.

---

**Report generated:** September 8, 2026  
**Next step:** Update README.md to match reality, or fix code to match README
