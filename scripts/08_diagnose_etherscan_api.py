"""
Diagnose Etherscan API issue - check raw responses for ONE wallet
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

# Test wallet from test split
test_address = '0x490d29b8669823e12eb5f72d53c27ebe7f952ab4'

print("="*80)
print("ETHERSCAN API DIAGNOSTIC")
print("="*80)
print(f"\nTest address: {test_address}")
print(f"API key present: {'Yes' if ETHERSCAN_API_KEY else 'No'}")
print(f"API key length: {len(ETHERSCAN_API_KEY) if ETHERSCAN_API_KEY else 0}")

base_url = "https://api.etherscan.io/api"

# Test 1: txlist
print("\n[1/3] Testing txlist (normal transactions)...")
params_normal = {
    'module': 'account',
    'action': 'txlist',
    'address': test_address,
    'startblock': 0,
    'endblock': 99999999,
    'sort': 'asc',
    'apikey': ETHERSCAN_API_KEY
}

try:
    resp = requests.get(base_url, params=params_normal, timeout=10)
    data = resp.json()
    print(f"  HTTP Status: {resp.status_code}")
    print(f"  Response status: {data.get('status', 'N/A')}")
    print(f"  Response message: {data.get('message', 'N/A')}")
    result = data.get('result', [])
    if isinstance(result, list):
        print(f"  Result length: {len(result)}")
        if len(result) > 0:
            print(f"  First tx keys: {list(result[0].keys())[:5]}")
    else:
        print(f"  Result: {result}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: txlistinternal
print("\n[2/3] Testing txlistinternal (internal transactions)...")
params_internal = {
    'module': 'account',
    'action': 'txlistinternal',
    'address': test_address,
    'startblock': 0,
    'endblock': 99999999,
    'sort': 'asc',
    'apikey': ETHERSCAN_API_KEY
}

try:
    resp = requests.get(base_url, params=params_internal, timeout=10)
    data = resp.json()
    print(f"  HTTP Status: {resp.status_code}")
    print(f"  Response status: {data.get('status', 'N/A')}")
    print(f"  Response message: {data.get('message', 'N/A')}")
    result = data.get('result', [])
    if isinstance(result, list):
        print(f"  Result length: {len(result)}")
    else:
        print(f"  Result: {result}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: tokentx
print("\n[3/3] Testing tokentx (ERC20 transfers)...")
params_erc20 = {
    'module': 'account',
    'action': 'tokentx',
    'address': test_address,
    'startblock': 0,
    'endblock': 99999999,
    'sort': 'asc',
    'apikey': ETHERSCAN_API_KEY
}

try:
    resp = requests.get(base_url, params=params_erc20, timeout=10)
    data = resp.json()
    print(f"  HTTP Status: {resp.status_code}")
    print(f"  Response status: {data.get('status', 'N/A')}")
    print(f"  Response message: {data.get('message', 'N/A')}")
    result = data.get('result', [])
    if isinstance(result, list):
        print(f"  Result length: {len(result)}")
    else:
        print(f"  Result: {result}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)
