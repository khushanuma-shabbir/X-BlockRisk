# Project Structure

Clean, organized structure for the Blockchain Fraud Detection system.

---

## 📁 Root Directory

```
CAPSTONE PROJECT/
├── 📄 README.md                      # Main project documentation & setup instructions
├── 📄 requirements.txt               # Python dependencies
├── 📄 .env                           # API keys (ETHERSCAN_API_KEY, SOLANA_API_KEY)
├── 📄 .gitignore                     # Git ignore rules
│
├── 📄 LIMITATIONS.md                 # Model scope & limitations documentation
├── 📄 RETAIL_FRAUD_TEST_NOTE.md     # Explanation of data limitations
├── 📄 FINAL_VALIDATION.md           # Final testing & validation report
│
├── 🧪 test_simple.py                 # Simple test script for quick validation
├── 🧪 test_synthetic_capability.py  # Ethereum synthetic capability tests
├── 🧪 test_solana_synthetic.py      # Solana synthetic capability tests
│
├── 📂 config/                        # Configuration files
│   ├── data_paths.py                # Path configurations
│   └── feature_columns.py           # Feature definitions (prevents mismatches)
│
├── 📂 src/                           # Main source code
│   ├── app.py                       # 🚀 STREAMLIT DASHBOARD (main entry point)
│   ├── __init__.py
│   │
│   ├── 📂 data_pipeline/            # Data processing pipeline (Steps 1-6)
│   │   ├── 01_discover_data.py     # Data discovery
│   │   ├── 02_explore_data.py      # Data exploration
│   │   ├── 03_clean_data.py        # Data cleaning & feature engineering
│   │   ├── 04_label_data.py        # Label assignment
│   │   ├── 05_build_graphs.py      # Graph construction
│   │   └── 06_split_data.py        # Train/val/test split
│   │
│   ├── 📂 models/                   # Model training & explanation (Step 7-8)
│   │   ├── train_gnn.py            # GraphSAGE model training
│   │   └── explain_gnn.py          # Model explainability (GNNExplainer)
│   │
│   ├── 📂 live/                     # Live data fetching (Step 8)
│   │   ├── fetch_ethereum.py       # Etherscan API integration
│   │   └── fetch_solana.py         # Solana API integration
│   │
│   ├── 📂 utils/                    # Utility functions
│   └── 📂 visualization/            # Plotting utilities
│
├── 📂 data/                         # Data storage
│   ├── 📂 raw/                     # Original datasets (Kaggle, Solana scraping)
│   ├── 📂 interim/                 # Intermediate processing outputs
│   ├── 📂 processed/               # Final clean datasets
│   │   ├── ethereum_clean.csv      # 9,288 labeled Ethereum wallets
│   │   ├── ethereum_graph.pt       # Ethereum graph (PyTorch Geometric)
│   │   ├── solana_labeled.csv      # 116,304 labeled Solana pools
│   │   └── solana_graph.pt         # Solana graph (PyTorch Geometric)
│   └── 📂 splits/                  # Train/val/test splits
│
├── 📂 models/                       # Trained models
│   ├── 📂 ethereum/
│   │   ├── model.pt                # Trained GraphSAGE weights
│   │   ├── scaler.pkl              # Feature scaler
│   │   └── training_log.txt        # Training history
│   └── 📂 solana/
│       ├── model.pt                # Trained GraphSAGE weights
│       ├── scaler.pkl              # Feature scaler
│       └── training_log.txt        # Training history
│
├── 📂 results/                      # Training results & visualizations
│   ├── 📂 confusion_matrices/      # Model performance matrices
│   ├── 📂 evaluation_reports/      # Detailed evaluation metrics
│   ├── 📂 shap_plots/              # Feature importance plots
│   └── example_explanations.txt    # Sample model explanations
│
└── 📂 test_data/                    # Test validation data
    ├── README_TEST_CASES.md        # 📋 COMPREHENSIVE TEST DOCUMENTATION
    ├── ethereum_synthetic_results.txt
    └── solana_synthetic_results.txt
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Keys
Create `.env` file:
```
ETHERSCAN_API_KEY=your_key_here
SOLANA_API_KEY=your_key_here
```

### 3. Run Dashboard
```bash
cd src
streamlit run app.py
```

### 4. Test System
```bash
python test_simple.py
```

---

## 📊 Key Files Explained

### Main Application
- **`src/app.py`** - Streamlit dashboard (Step 9)
  - Input: Ethereum address or Solana pool
  - Output: Risk score, category, explanation
  - Features: Live API integration, GNN inference, humanized output

### Data Pipeline (Steps 1-6)
Run in order to reproduce training:
```bash
cd src/data_pipeline
python 01_discover_data.py
python 02_explore_data.py
python 03_clean_data.py
python 04_label_data.py
python 05_build_graphs.py
python 06_split_data.py
```

### Model Training (Step 7)
```bash
cd src/models
python train_gnn.py
python explain_gnn.py
```

### Live Integration (Step 8)
- **`fetch_ethereum.py`** - Fetches wallet transaction history from Etherscan V2 API
- **`fetch_solana.py`** - Fetches pool liquidity data from Solana API

### Testing
- **`test_simple.py`** - Quick test with Vitalik's address
- **`test_synthetic_capability.py`** - Validates model logic on synthetic patterns
- **`test_solana_synthetic.py`** - Validates Solana model

---

## 📚 Documentation

### Must-Read Documentation
1. **`README.md`** - Project overview, setup, usage
2. **`LIMITATIONS.md`** - Model scope & what it CAN/CANNOT detect
3. **`test_data/README_TEST_CASES.md`** - All test cases & validation results
4. **`FINAL_VALIDATION.md`** - Final testing report

### Technical Documentation
- **`RETAIL_FRAUD_TEST_NOTE.md`** - Explains training data address limitation
- **`config/feature_columns.py`** - Feature definitions (prevents bugs)

---

## 🎯 Training Data

### Ethereum
- **Source:** Kaggle Ethereum Wallet Fraud Detection Dataset
- **File:** `data/processed/ethereum_clean.csv`
- **Size:** 9,288 wallets (1,656 fraud, 7,632 legit)
- **Features:** 38 transaction-based features
- **Performance:** 94.3% ROC-AUC

### Solana
- **Source:** Custom-scraped liquidity pool dataset
- **File:** `data/processed/solana_labeled.csv`
- **Size:** 116,304 pools (10,527 rugpulls, 105,777 legit)
- **Features:** 7 liquidity-based features
- **Performance:** 91.5% ROC-AUC

---

## 🔧 Configuration

### Feature Columns (Important!)
`config/feature_columns.py` defines exact feature order.
**DO NOT modify** unless retraining models.

### Data Paths
`config/data_paths.py` contains all file paths.
Modify if changing directory structure.

---

## ⚠️ Important Notes

### What This System Does
✅ Detects retail-level wallet fraud (phishing, small scams)  
✅ Detects Solana liquidity pool rug-pulls  
✅ Provides explainable risk scores  
✅ Works with live blockchain data  

### What It Does NOT Do
❌ Detect large-scale exploits (Ronin Bridge, etc.)  
❌ Detect smart contract vulnerabilities  
❌ Provide financial advice  
❌ Work without API keys  

See `LIMITATIONS.md` for full details.

---

## 📞 Support

**Issues?**
1. Check `README.md` setup instructions
2. Verify API keys in `.env`
3. Run `python test_simple.py` to diagnose
4. See `test_data/README_TEST_CASES.md` for expected behavior

**Performance Issues?**
- Model trained on retail fraud patterns
- Large wallets (>10K ETH) trigger safety warnings
- See `LIMITATIONS.md` for scope

---

**Last Updated:** September 1, 2026  
**Version:** 1.0  
**Status:** ✅ Production Ready
