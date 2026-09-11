# Blockchain Fraud Detection System

## The Problem

Crypto scams are everywhere. Two common types:

1. Someone's Ethereum wallet is being used for fraud/scamming people
2. A "rug pull" — someone creates a fake crypto token on Solana, lets people invest, then drains all the money and disappears

Most tools that try to catch these are just simple rule-checkers. This project is smarter — it uses AI that actually learns patterns from thousands of real examples, and — importantly — it explains its reasoning in plain English instead of just spitting out "risky" with no explanation.

## What This Project Does, Step by Step

1. **Real data.** One dataset has ~9,300 real Ethereum wallets, each already labeled as "fraud" or "legit" by researchers. Another dataset has ~116,000 real Solana liquidity pools (the "money pot" behind every token) tracked from 2021-2024.

2. **Cleaned the data.** Raw data is messy — missing values, duplicates, junk columns. Scripts were written to fix all of that.

3. **Created labels where none existed.** Since Solana had no "this is a scam" labels, a rule was designed to create them: if someone added liquidity, then yanked almost all of it back out and vanished, that's a rug pull. This produced ~10,500 labeled rug pulls to learn from.

4. **Built a graph — literally connecting the dots.** Instead of looking at wallets/pools one at a time in isolation, they're connected like a social network: wallets that behave similarly are linked together, and Solana pools that share the same token are linked together. This matters because scammers often aren't acting alone — they're connected to other scam wallets/pools.

5. **Trained a Graph Neural Network (GNN)** — an AI model that doesn't just look at one wallet's numbers, but also looks at who it's connected to. If a wallet looks slightly suspicious AND is connected to other known-bad wallets, that's a much stronger signal than either fact alone.

6. **Made it explainable.** Instead of just saying "87% risky," it tells you why — e.g., "this wallet sends money unusually fast to many addresses" or "this pool's owner pulled almost all the liquidity right after launch." This is the "Explainable AI" part — no black box.

7. **Connected it to the real world.** Using Etherscan's API and a Solana explorer API, anyone can type in a real wallet address or transaction ID, and the system fetches that wallet's actual live history from the blockchain, runs it through the trained model, and gives a live risk score — not just data from the training files.

8. **Built a simple dashboard.** One webpage: type in an address, hit "Analyze," and see a risk score, a risk category (Low/Medium/High), and a plain-English explanation.

9. **Honest about its limits.** Testing found that the model is really good at catching small-scale, retail-level scams (the kind the training data has lots of examples of), but it's not built to catch giant, sophisticated attacks like the $625M Ronin Bridge hack — because nothing like that was in the training data. Rather than hiding this, it's documented clearly in LIMITATIONS.md.

## In One Sentence

This system looks at real blockchain wallets and liquidity pools as a connected network, uses a graph neural network to spot scam patterns based on both a wallet's own behavior and who it's connected to, explains its reasoning in plain English instead of being a black box, and lets anyone check a live, real wallet or pool — while being transparent that it's tuned for everyday retail scams rather than massive coordinated attacks.

---

## Performance Metrics

### Ethereum Fraud Detection (Augmented Model)

**After data augmentation to handle high-activity wallets:**
- **F1-Score: 83.04%** (improved from 75.51%)
- **Precision: 80.18%** (of 100 fraud warnings, 80 are correct)
- **Recall: 86.11%** (catches 86% of actual fraud)
- **Accuracy: 91.36%**
- **ROC-AUC: 96.69%**

**Training Data:** 40,464 samples (augmented from 9,288)

### Solana Rug-Pull Detection (Tuned Model)

- **F1-Score: 54.58%**
- **Precision: 40.68%** (conservative - catches most rug-pulls with some false positives)
- **Recall: 82.90%** (catches 83% of actual rug-pulls)
- **Accuracy: 87.51%**
- **ROC-AUC: 91.96%**

**Training Data:** 116,304 liquidity pools

**Note:** ROC-AUC measures the model's ability to discriminate between classes (like a ranking test), while accuracy/precision/recall measure actual classification performance. Both are important but measure different things.

---

## How to Run

### Prerequisites

- Python 3.11+
- pip package manager

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up API keys:**

Create a `.env` file in the project root:

```env
ETHERSCAN_API_KEY=your_etherscan_api_key_here
HELIUS_API_KEY=your_helius_api_key_here
```

**How to get API keys:**
- Etherscan: https://etherscan.io/apis (free tier available)
- Helius (Solana): https://www.helius.dev/ (free tier available)

3. **Launch the dashboard:**
```bash
cd src
streamlit run app.py
```

4. **Open in browser:**
```
http://localhost:8501
```

---

## Project Structure

```
project/
├── src/
│   ├── app.py                    # Main Streamlit dashboard
│   ├── live/
│   │   ├── fetch_ethereum.py     # Ethereum live API
│   │   └── fetch_solana.py       # Solana live API
│   ├── data_pipeline/
│   │   └── 03_label_solana.py    # Solana rug-pull labeling
│   └── models/
│       └── train_gnn.py          # Model training script
├── models/
│   ├── ethereum/
│   │   ├── model_augmented.pt    # Trained Ethereum model
│   │   └── scaler_augmented.pkl  # Feature scaler
│   └── solana/
│       ├── model_tuned.pt        # Trained Solana model
│       └── scaler.pkl            # Feature scaler
├── data/
│   └── processed/
│       ├── ethereum_augmented.csv
│       ├── ethereum_graph_augmented.pt
│       ├── solana_labeled.csv
│       └── solana_graph.pt
├── test_data/
│   ├── MASTER_TEST_CASES.csv     # 135 test cases
│   ├── run_master_tests.py       # Test runner
│   └── TEST_RESULTS.csv          # Test results
├── scripts/
│   ├── create_augmented_training_data.py
│   └── retrain_on_augmented_data.py
├── config/
│   └── feature_columns.py        # Feature definitions
├── docs/
│   └── LIMITATIONS.md            # Model limitations
├── README.md                     # This file
└── requirements.txt              # Python dependencies
```

---

## Testing

The project includes a comprehensive test suite with 135 test cases:

```bash
python test_data/run_master_tests.py
```

**Expected output:** 135/135 tests passed

---

## Known Issues

### Solana Live API - Partial Implementation

**Status:** The Solana live API connection works, but liquidity event parsing is not fully implemented.

**Current behavior:**
- API connects to Helius RPC successfully
- Transaction history is fetched
- **Liquidity events are NOT parsed** - uses heuristic placeholders instead

**Workaround for demonstration:**
- Use **Synthetic Test Mode** in the dashboard
- 100 pre-computed test cases available
- Shows real model predictions on realistic data

**Technical details:**
- Location: `src/live/fetch_solana.py`, lines 68-86 and 195-203
- Issue: DEX-specific instruction parsing (Raydium/Orca/Jupiter) not implemented
- Each DEX has different binary instruction formats
- Implementing full parser requires 4-8 hours of development

**Future work:** Implement proper instruction parsing for major Solana DEXes.

---

## Documentation

- **LIMITATIONS.md** - Honest assessment of what the model can and cannot detect
- **test_data/README_TEST_CASES.md** - Test case documentation
- **docs/** - Additional technical documentation

---

## Model Architecture

- **Algorithm:** GraphSAGE (Graph Neural Network)
- **Layers:** 3-layer with hidden dimension 64, dropout 0.4
- **Loss Function:** 
  - Ethereum: Focal Loss (gamma=1.0)
  - Solana: Weighted Cross-Entropy
- **Optimization:** Threshold tuning via validation set
  - Ethereum: 0.55
  - Solana: 0.65

---

## What This Model Can Detect

### Ethereum:
✅ Retail-level phishing attacks  
✅ Small-scale scam operations  
✅ Suspicious transaction patterns  
✅ Active fraud wallets (those that send transactions)

❌ Large-scale exploits (e.g., Ronin Bridge hack)  
❌ Smart contract vulnerabilities  
❌ Passive scam addresses (receive-only)

### Solana:
✅ Classic rug-pull patterns  
✅ Liquidity removal scams  
✅ Abandoned pools with suspicious behavior

❌ Sophisticated multi-pool operations  
❌ Novel rug-pull strategies not in training data

See **docs/LIMITATIONS.md** for detailed discussion.

---

## License

This project is for educational and research purposes.

---

## Acknowledgments

- Ethereum fraud dataset: Kaggle (labeled by researchers)
- Solana data: Custom collection (2021-2024)
- Framework: PyTorch Geometric, Streamlit

---

**Last Updated:** September 2026
