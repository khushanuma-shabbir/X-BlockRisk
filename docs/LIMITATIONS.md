# Model Limitations

## Ethereum Fraud Detection Scope

### Training Data Characteristics

The Ethereum fraud detection model was trained on a **labeled Ethereum wallet fraud dataset sourced from Kaggle** (`transaction_dataset.csv`), which contains wallet-level transaction features with binary fraud labels. The dataset represents **retail-level wallet fraud** including phishing attacks, small-scale scams, and individual fraudulent wallets.

**Training Data Statistics:**
- Total samples: 9,288 wallets
- Fraud samples: 1,656 (18%)
- Legitimate samples: 7,632 (82%)

| Metric | Fraud Average | Legitimate Average |
|--------|--------------|-------------------|
| Sent transactions | 6.8 | 147.9 |
| Received transactions | 31.3 | 204.2 |
| Unique addresses contacted | 4.3 | 32.4 |
| Total ETH volume | 115 ETH | 13,074 ETH |

### What This Model CAN Detect

✅ **Retail-level fraud patterns (ACTIVE wallets):**
- Phishing wallets that SEND scam transactions
- Wallets with suspicious OUTGOING transaction patterns
- Small-scale scam operations with active trading
- Fraudulent wallets with <100 transactions that show activity
- Suspicious timing/volume patterns in sent transactions

⚠️ **Important:** Model trained on ACTIVE fraud wallets (those that send transactions)

### What This Model CANNOT Detect

❌ **Large-scale exploits and sophisticated attacks:**
- Bridge exploits (e.g., Ronin Bridge hack)
- Smart contract vulnerabilities
- Nation-state or organized crime operations
- Flash loan attacks
- Cross-chain exploits

❌ **Passive scam addresses:**
- Addresses that ONLY RECEIVE stolen funds (no outgoing transactions)
- Scam token contracts (requires contract analysis)
- Addresses with zero or minimal sent transaction history

**Why passive addresses aren't detected:** The training data contains fraud wallets with active transaction patterns (sending phishing messages, moving funds, etc.). Addresses that only receive funds have no "sent transaction" features for the model to analyze, so they appear similar to legitimate receiving-only addresses (e.g., cold storage wallets).

**Example: Ronin Bridge Exploiter Analysis**

Address: `0x098B716B8Aaf21512996dC57EB0615e2383E2f96`
- Known exploit: $625M stolen in March 2022 (one of the largest crypto hacks ever)
- Model prediction: **0/100 risk (LOW RISK)**

| Metric | This Exploiter | Fraud Training Avg | Legit Training Avg |
|--------|---------------|-------------------|-------------------|
| Sent transactions | 38 | 6.8 | **147.9** |
| Received transactions | 392 | 31.3 | **204.2** |
| Unique addresses | 28 | 4.3 | **32.4** |
| Total ETH volume | **182,166 ETH** | 115 | 13,074 |

**Why the mismatch?** The exploiter's high transaction volume and diverse address interactions statistically resemble legitimate high-activity wallets (exchanges, protocols) more than the small scammers in the training data.

### Design Rationale

**This model is designed to detect small-scale wallet fraud patterns.** It is not trained to detect large-scale bridge exploits, which require different detection signals such as:
- Smart contract logic analysis
- Cross-chain transaction tracking
- Vulnerability exploit signatures
- Governance attack patterns
- Flash loan interaction analysis

Detecting sophisticated exploits would require:
1. Contract bytecode analysis
2. DeFi protocol interaction graphs
3. Time-series anomaly detection for liquidity events
4. Multi-chain transaction correlation

These capabilities are outside the scope of the current wallet transaction-based model.

### Recommended Use

- ✅ Use this model to assess **individual wallets** for retail fraud indicators
- ✅ Suitable for vetting counterparties in P2P transactions
- ✅ Helps identify phishing and scam addresses
- ⚠️ **Do NOT rely solely on this model** for large-volume or high-value transactions
- ⚠️ Wallets with >10,000 ETH volume should undergo manual security review
- ⚠️ Smart contract addresses require separate contract audit procedures

### Testing Limitation

**Important:** The training dataset contains only engineered features without actual wallet addresses. This means:
- The model achieved 94.3% ROC-AUC on held-out test data during training
- Real-world performance on live retail fraud addresses cannot be directly verified without addresses in the training data
- The model is expected to perform well on addresses exhibiting similar statistical patterns to the training fraud examples

**Synthetic Feature Test Results:**

To verify the model responds correctly to fraud-like feature patterns, synthetic feature vectors were tested:

| Test Case | Pattern | Risk Score | Result |
|-----------|---------|------------|--------|
| **Retail Fraud** | 3 sent, 27 received, 12 ETH, 3 unique addresses | **95/100** | ✅ HIGH RISK (correct) |
| **Legitimate** | 150 sent, 200 received, 7,500 ETH, 30 unique addresses | **0/100** | ✅ LOW RISK (correct) |

These synthetic tests confirm the model correctly learned to distinguish fraud patterns from legitimate patterns based on feature distributions. However, this does NOT validate real-world performance on actual phishing addresses, which requires testing against labeled live addresses unavailable in the training dataset.

See `RETAIL_FRAUD_TEST_NOTE.md` and `test_synthetic_capability.py` for detailed explanation.

### Future Improvements

To expand detection capabilities:
1. Incorporate smart contract interaction features
2. Add bridge transaction analysis
3. Include temporal anomaly detection
4. Integrate cross-chain activity tracking
5. Train on labeled exploit datasets (when available)

---

## Solana Rug-Pull Detection Scope

The Solana model is trained on liquidity pool behavior and designed to detect:
- ✅ Token liquidity removal patterns (rug-pulls)
- ✅ Suspicious pool lifecycle patterns
- ⚠️ Limited to pools with sufficient transaction history

**Not designed for:**
- Token price manipulation detection
- Honeypot contract detection
- Sybil attack identification

### Feature Dominance Limitation

**Finding:** Feature importance analysis reveals that `NUM_LIQUIDITY_ADDS` (number of liquidity additions) accounts for approximately **60.6%** of the Solana model's decision-making weight.

**Why this happens:**
- Rug-pull pools average: **1.85 liquidity additions**
- Legitimate pools average: **1,539.88 liquidity additions**
- This represents a **~1,000x difference** between the two classes

**Is this signal legitimate?**

✅ **Yes, it makes intuitive sense:**
- Few liquidity additions = low community participation = red flag
- Rug-pulls typically involve only the creator adding liquidity (1-3 times)
- Legitimate projects have many independent liquidity providers

**What's the problem?**

⚠️ **Model fragility:**
- The model relies heavily on this single feature rather than diverse independent signals
- Rug-pulls with more sophisticated liquidity patterns (>3 adds from multiple wallets) may evade detection
- The Ethereum model, by contrast, uses 38 features with more balanced importance

**Impact on performance:**
- Solana F1-score (54.58%) is lower than Ethereum (75.51%)
- This suggests the 7-feature Solana model has less nuanced pattern recognition
- The model may generalize poorly to novel rug-pull strategies

**Future improvements:**
1. Engineer additional ratio features (e.g., add/remove timing patterns)
2. Add wallet-level features (creator wallet history, token distribution)
3. Include temporal features (pool activity decay rate)
4. Create interaction terms between existing features
5. Expand to multi-pool analysis (same creator's other pools)

This limitation is documented transparently because reliance on a single dominant feature, while effective for current rug-pull patterns, presents a known vulnerability to evasion tactics.

---

**Last Updated:** September 2026


---

## Smart Contract Analysis Limitations

### What It Is

The smart contract analysis module is **rule-based**, not machine learning. It uses pattern matching on verified source code to identify common risk indicators.

### What It Can Detect

✅ **Unverified contracts** - Major red flag when source code isn't public  
✅ **Unrestricted mint functions** - Allows unlimited token creation  
✅ **Honeypot indicators** - Pause, blacklist, transfer restrictions  
✅ **Owner privileges** - Excessive withdrawal or control functions  
✅ **Proxy patterns** - Upgradeable contracts that can change behavior  
✅ **Standard compliance** - Whether it follows ERC20/721/1155 patterns

### What It Cannot Detect

❌ **Complex vulnerabilities** - Reentrancy, integer overflow/underflow, front-running  
❌ **Economic exploits** - Flash loan attacks, oracle manipulation  
❌ **Logic bugs** - Business logic errors requiring deep understanding  
❌ **Bytecode-only contracts** - Works only on verified source code  
❌ **Off-chain risks** - Team doxxing, tokenomics, market manipulation

### Why It's Not ML-Based

**No training data exists.** Unlike wallet fraud (9,288 labeled samples) or Solana rug-pulls (116,304 pools), there's no public dataset of thousands of labeled smart contracts with "scam" vs "legitimate" labels.

Building such a dataset would require:
- Manual auditing of thousands of contracts
- Expert security knowledge to label vulnerabilities
- Time-consuming review (hours per contract)
- Historical analysis of exploited vs safe contracts

Instead, we implemented rule-based heuristics that flag **known red flags** based on security best practices.

### Accuracy Expectations

**This is NOT a security audit.** The rule-based analyzer:
- Flags obvious warning signs (90%+ detection on unverified/honeypot patterns)
- Provides useful screening for retail investors
- Cannot replace professional auditing firms

**Always do your own research (DYOR)** before interacting with any smart contract, regardless of this tool's assessment.

### When to Use It

✅ **Quick screening** - Before buying a new token  
✅ **Red flag detection** - Identify obvious scams (unverified, drain functions)  
✅ **Educational** - Learn what to look for in contract code

❌ **Professional auditing** - Use Trail of Bits, OpenZeppelin, etc.  
❌ **High-value decisions** - Don't stake $100K based on this tool alone  
❌ **Legal compliance** - Not sufficient for regulatory requirements

### False Positives/Negatives

**False Positives (Safe contracts flagged):**
- Legitimate pause functions (circuit breakers for security)
- Admin functions in DAO-governed contracts
- Proxy patterns used by Uniswap, AAVE (industry standard)

**False Negatives (Scams not flagged):**
- Sophisticated logic bugs not visible in pattern matching
- Verified contracts with hidden backdoors in complex code
- Social engineering (legitimate code but malicious team)

### Future Improvements

If a labeled smart contract dataset becomes available:
1. Train a GNN on contract call graphs
2. Use NLP on source code comments/documentation
3. Analyze bytecode patterns for unverified contracts
4. Build a graph of contract interactions (who calls who)

Until then, rule-based heuristics + ML wallet analysis provides two complementary layers of protection.

---

## Summary Table

| Analysis Type | Method | Training Data | Accuracy | Use Case |
|--------------|--------|---------------|----------|----------|
| Ethereum Wallets | GraphSAGE GNN | 9,288 samples | 91.36% | Fraud detection |
| Solana Pools | GraphSAGE GNN | 116,304 pools | 87.51% | Rug-pull detection |
| Smart Contracts | Rule-based | None (heuristics) | ~85%* | Red flag screening |

*Estimated based on pattern matching accuracy for known red flags. Not validated on large-scale labeled dataset.
