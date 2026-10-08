# Project Cleanup Plan

## Current State: MESSY (50+ files in root, 15+ MD files)

## Target State: CLEAN & ORGANIZED

```
CAPSTONE PROJECT/
├── src/                    # Core application code
├── models/                 # Trained ML models
├── data/                   # Datasets
├── static/                 # Web interface assets (CSS, JS)
├── templates/              # HTML templates
├── docs/                   # All documentation (MD files)
├── tests/                  # All test scripts
├── .env                    # Environment variables
├── .gitignore             # Git ignore rules
├── README.md              # Main project overview
├── requirements.txt       # Python dependencies
├── app_web.py            # Main web application
└── train_real_ml_model.py # ML training script
```

## Files to Move

### To docs/ (All documentation)
- ACTION_PLAN.md
- FINAL_VALIDATION_REPORT.md
- GNN_MODEL_LIMITATIONS.md
- HONEST_SYSTEM_ASSESSMENT.md
- OPTIONAL_IMPROVEMENTS.md
- PHASE_4_COMPLETE.md
- PRACTICAL_AI_FIX.md
- QUICK_REFERENCE.md
- QUICK_START_ML.md
- REAL_SOLUTION.md
- REPRODUCIBILITY_GUIDE.md
- SAFE_GNN_RETRAIN_PLAN.md
- TESTING_GUIDE.md
- TEST_COVERAGE_REPORT.md
- WORKING_EXAMPLES.md

### To tests/ (All test scripts)
- check_address.py
- demo_ml_detection.py
- run_comprehensive_tests.py
- test_coingecko_liquidity.py
- test_context_aware.py
- test_dex_analyzer.py
- test_etherscan_abi.py
- test_gnn_confidence.py
- test_offline_reproduction.py
- test_on_dataset.py
- test_real_addresses.py
- test_synthetic_only.py
- verify_all_features.py

### To DELETE (Temporary/duplicate)
- archive/ (old versions)
- scripts/ (if empty or duplicates)
- test_data/ (if not needed)
- .vscode/ (IDE settings, not needed for project)
- check_address.py (temporary file)
- start_app.bat (not needed, use python app_web.py)
- restart_app.bat (not needed)
- .env.example (if duplicate of .env)

### KEEP in root (Essential only)
- .env
- .gitignore
- README.md
- requirements.txt
- app_web.py
- train_real_ml_model.py
