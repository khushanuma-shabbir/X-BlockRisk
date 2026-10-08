"""Test Etherscan ABI fetch for USDT"""
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ETHERSCAN_API_KEY')
usdt = '0xdAC17F958D2ee523a2206206994597C13D831ec7'

print(f"Testing USDT: {usdt}")
print(f"API Key: {api_key[:8]}..." if api_key else "No API Key")

params = {
    'chainid': '1',  # Ethereum mainnet
    'module': 'contract',
    'action': 'getabi',
    'address': usdt,
    'apikey': api_key
}

# Try V2 API first
response = requests.get('https://api.etherscan.io/v2/api', params=params, timeout=10)
print(f"V2 Response status: {response.status_code}")

data = response.json()
print(f"V2 Response preview: {str(data)[:500]}")

if response.status_code != 200 or data.get('status') == '0':
    print("\nV2 failed, trying V1...")
    response = requests.get('https://api.etherscan.io/api', params=params, timeout=10)
    data = response.json()


print(f"\nStatus: {data.get('status')}")
print(f"Message: {data.get('message')}")
print(f"Result type: {type(data.get('result'))}")

if data.get('result'):
    result_str = data.get('result')
    print(f"Result length: {len(result_str)} chars")
    print(f"Result content: {result_str}")
    
    # Try to parse as JSON
    try:
        abi = json.loads(result_str)
        print(f"ABI parsed: {len(abi)} items")
        
        # Look for specific functions
        functions = [item for item in abi if item.get('type') == 'function']
        print(f"Functions found: {len(functions)}")
        
        # Check for admin functions
        admin_functions = []
        for func in functions:
            name = func.get('name', '').lower()
            if any(keyword in name for keyword in ['pause', 'blacklist', 'mint', 'addblacklist', 'deprecate']):
                admin_functions.append(func.get('name'))
        
        print(f"\nAdmin functions found: {admin_functions}")
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
else:
    print("No result returned")
