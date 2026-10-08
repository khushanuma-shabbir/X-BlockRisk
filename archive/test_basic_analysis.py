"""
Simple test to verify the fraud detection system works
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("TESTING FRAUD DETECTION SYSTEM")
print("="*80)

# Test 1: Check imports
print("\n[TEST 1] Checking imports...")
try:
    from src.live.fetch_ethereum import fetch_ethereum_wallet
    print("✓ fetch_ethereum_wallet imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Check models
print("\n[TEST 2] Checking models...")
try:
    import torch
    model_path = "models/ethereum_clean/gnn_22feat.pt"
    if os.path.exists(model_path):
        print(f"✓ Model found: {model_path}")
    else:
        print(f"✗ Model not found: {model_path}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Model check failed: {e}")
    sys.exit(1)

# Test 3: Check Etherscan API key
print("\n[TEST 3] Checking API configuration...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('ETHERSCAN_API_KEY', '')
    if api_key:
        print(f"✓ Etherscan API key found (length: {len(api_key)})")
    else:
        print("✗ WARNING: No Etherscan API key found in .env file")
        print("  The analysis might fail without an API key")
except Exception as e:
    print(f"✗ API check failed: {e}")

# Test 4: Test address validation
print("\n[TEST 4] Testing address validation...")
try:
    from src.live.fetch_ethereum import InputValidator
    
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    valid, normalized, error = InputValidator.validate_ethereum_address(test_address)
    
    if valid:
        print(f"✓ Address validation works")
        print(f"  Input:      {test_address}")
        print(f"  Normalized: {normalized}")
    else:
        print(f"✗ Validation failed: {error}")
except Exception as e:
    print(f"✗ Validation test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Try a simple API call (with timeout)
print("\n[TEST 5] Testing Etherscan API connection...")
try:
    import requests
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('ETHERSCAN_API_KEY', '')
    if not api_key:
        print("⚠ Skipping API test - no API key configured")
    else:
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        
        params = {
            'chainid': '1',
            'module': 'account',
            'action': 'balance',
            'address': test_address,
            'apikey': api_key
        }
        
        print(f"  Testing API connection...")
        response = requests.get(
            "https://api.etherscan.io/v2/api",
            params=params,
            timeout=10
        )
        
        data = response.json()
        
        if data.get('status') == '1':
            balance = int(data.get('result', 0)) / 1e18
            print(f"✓ API connection works!")
            print(f"  Test address balance: {balance:.4f} ETH")
        else:
            print(f"✗ API returned error: {data.get('message', 'Unknown error')}")
            print(f"  Result: {data.get('result', 'N/A')}")
            
except Exception as e:
    print(f"✗ API test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Try fetching wallet data
print("\n[TEST 6] Testing wallet data fetch (this may take 10-30 seconds)...")
try:
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    
    print(f"  Fetching data for: {test_address}")
    print(f"  Please wait...")
    
    features, is_contract, flags, source = fetch_ethereum_wallet(test_address)
    
    if features:
        print(f"✓ Wallet data fetched successfully!")
        print(f"  Features extracted: {len(features)}")
        print(f"  Data source: {source}")
        print(f"  Sample features:")
        for i, (key, value) in enumerate(list(features.items())[:5]):
            print(f"    - {key}: {value}")
    else:
        print(f"✗ No features returned")
        print(f"  Flags: {flags}")
        
except Exception as e:
    print(f"✗ Wallet fetch failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\nIf all tests passed, your system is working correctly!")
print("If any tests failed, check the error messages above.")
