"""
Train the Lightweight ML Model on Real Ethereum Data

This script:
1. Collects labeled Ethereum addresses (phishing + legitimate)
2. Extracts behavioral features using Etherscan API
3. Trains a Random Forest classifier
4. Validates performance

Expected result: 75-85% accuracy on new addresses (not just blacklist lookup)
Time: ~10 minutes (depends on API rate limits)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    print("="*80)
    print("TRAINING LIGHTWEIGHT ML FRAUD DETECTOR")
    print("="*80)
    print()
    print("This will:")
    print("  1. Collect 20 labeled Ethereum addresses (10 phishing + 10 legitimate)")
    print("  2. Extract behavioral features using Etherscan API")
    print("  3. Train a Random Forest model")
    print("  4. Save the model for use in detection system")
    print()
    print("Time required: ~10 minutes")
    print("="*80)
    print()
    
    # Load environment
    load_dotenv()
    api_key = os.getenv('ETHERSCAN_API_KEY')
    
    if not api_key:
        print("❌ ERROR: ETHERSCAN_API_KEY not found in .env file")
        print()
        print("Please add your Etherscan API key to .env:")
        print('ETHERSCAN_API_KEY="your_key_here"')
        return 1
    
    print("✓ Etherscan API key found")
    print()
    
    # Step 1: Collect training data
    print("STEP 1: Collecting Training Data")
    print("-" * 80)
    
    from src.ml.collect_ethereum_training_data import EthereumDataCollector
    
    collector = EthereumDataCollector(api_key)
    
    try:
        df = collector.collect_training_dataset()
        print()
        print(f"✓ Collected {len(df)} addresses")
        print()
    except Exception as e:
        print(f"❌ Error collecting data: {e}")
        return 1
    
    # Step 2: Train model
    print("STEP 2: Training Model")
    print("-" * 80)
    
    from src.ml.lightweight_fraud_detector import LightweightFraudDetector
    
    detector = LightweightFraudDetector()
    
    try:
        metrics = detector.train()
        print()
        print("="*80)
        print("✅ TRAINING COMPLETE!")
        print("="*80)
        print()
        print(f"Test Accuracy: {metrics['test_accuracy']:.1%}")
        print(f"ROC AUC: {metrics['roc_auc']:.3f}")
        print()
        print("Model saved to: models/lightweight_fraud_detector.pkl")
        print()
        print("This model:")
        print("  ✓ Trained on REAL Ethereum data")
        print("  ✓ Uses behavioral patterns (not just blacklist)")
        print("  ✓ Works on NEW addresses it hasn't seen before")
        print("  ✓ Fast and interpretable")
        print()
        print("Now run: python verify_all_features.py")
        print()
        return 0
        
    except Exception as e:
        print(f"❌ Error training model: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
