"""
Live Ethereum Wallet Data Fetcher
Fetches transaction history and computes fraud detection features
"""

import requests
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import sys

# Add parent directory for config imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from config.feature_columns import ETHEREUM_FEATURE_COLUMNS, validate_feature_dict
from src.live.scaler_aware_clipping import clip_features_for_scaler

load_dotenv()

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')
ETHERSCAN_BASE_URL = "https://api.etherscan.io/v2/api"  # V2 endpoint


def resolve_tx_to_address(tx_hash):
    """Resolve transaction hash to sender address"""
    try:
        response = requests.get(ETHERSCAN_BASE_URL, params={
            'module': 'proxy',
            'action': 'eth_getTransactionByHash',
            'txhash': tx_hash,
            'apikey': ETHERSCAN_API_KEY
        }, timeout=10)
        
        data = response.json()
        if data.get('result'):
            return data['result'].get('from')
        return None
    except Exception as e:
        print(f"Error resolving tx hash: {e}")
        return None


def fetch_wallet_transactions(address):
    """Fetch normal transactions for wallet using Etherscan V2 API"""
    try:
        params = {
            'chainid': '1',  # Ethereum mainnet
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': '0',
            'endblock': '99999999',
            'page': '1',
            'offset': '10000',
            'sort': 'asc',
            'apikey': ETHERSCAN_API_KEY
        }
        
        print(f"[DEBUG] Calling Etherscan V2 API...")
        print(f"[DEBUG] URL: {ETHERSCAN_BASE_URL}")
        print(f"[DEBUG] API Key (first 4 chars): {ETHERSCAN_API_KEY[:4] if ETHERSCAN_API_KEY else 'None'}...")
        print(f"[DEBUG] Address: {address}")
        
        response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10)
        
        print(f"[DEBUG] HTTP Status Code: {response.status_code}")
        print(f"[DEBUG] Raw Response (first 500 chars): {response.text[:500]}...")
        
        data = response.json()
        print(f"[DEBUG] Parsed JSON status: {data.get('status')}")
        print(f"[DEBUG] Parsed JSON message: {data.get('message')}")
        print(f"[DEBUG] Result count: {len(data.get('result', [])) if isinstance(data.get('result'), list) else 'N/A'}")
        
        if data.get('status') == '1' and data.get('result'):
            print(f"[SUCCESS] Fetched {len(data['result'])} transactions")
            return pd.DataFrame(data['result'])
        else:
            print(f"[INFO] API returned status={data.get('status')}, message={data.get('message')}")
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Exception in fetch_wallet_transactions: {type(e).__name__}: {e}")
        return pd.DataFrame()


def fetch_erc20_transactions(address):
    """Fetch ERC20 token transactions using V2 API"""
    try:
        params = {
            'chainid': '1',
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'page': '1',
            'offset': '10000',
            'startblock': '0',
            'endblock': '99999999',
            'sort': 'asc',
            'apikey': ETHERSCAN_API_KEY
        }
        
        response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10)
        
        data = response.json()
        if data.get('status') == '1' and data.get('result'):
            print(f"[SUCCESS] Fetched {len(data['result'])} ERC20 transactions")
            return pd.DataFrame(data['result'])
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Error fetching ERC20 transactions: {e}")
        return pd.DataFrame()


def check_contract_source(address):
    """Check if address is a contract and analyze source code"""
    try:
        response = requests.get(ETHERSCAN_BASE_URL, params={
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'apikey': ETHERSCAN_API_KEY
        }, timeout=10)
        
        data = response.json()
        if data.get('status') == '1' and data.get('result'):
            source_code = data['result'][0].get('SourceCode', '')
            
            red_flags = []
            if source_code:
                # Simple keyword-based red flags
                if 'onlyOwner' in source_code and 'mint' in source_code.lower():
                    red_flags.append("Owner-only mint function detected")
                if 'renounceOwnership' not in source_code and 'owner' in source_code.lower():
                    red_flags.append("No renounceOwnership function found")
                if 'selfdestruct' in source_code.lower():
                    red_flags.append("Self-destruct capability present")
                
                return True, red_flags
            return False, []
        return False, []
    except Exception as e:
        print(f"Error checking contract: {e}")
        return False, []


def compute_features(address, txs, erc20_txs):
    """
    Compute the SAME 38 features used in ethereum_clean.csv
    """
    features = {}
    
    if txs.empty:
        # Return zero features if no data
        return {f'feature_{i}': 0.0 for i in range(38)}
    
    # Convert to numeric
    txs['value'] = pd.to_numeric(txs['value'], errors='coerce') / 1e18  # Wei to ETH
    txs['timeStamp'] = pd.to_numeric(txs['timeStamp'], errors='coerce')
    
    # Separate sent vs received
    sent_txs = txs[txs['from'].str.lower() == address.lower()]
    received_txs = txs[txs['to'].str.lower() == address.lower()]
    
    # Time-based features
    if len(sent_txs) > 1:
        sent_times = sent_txs['timeStamp'].diff().dropna() / 60  # minutes
        features['Avg min between sent tnx'] = sent_times.mean() if len(sent_times) > 0 else 0
    else:
        features['Avg min between sent tnx'] = 0
    
    if len(received_txs) > 1:
        received_times = received_txs['timeStamp'].diff().dropna() / 60
        features['Avg min between received tnx'] = received_times.mean() if len(received_times) > 0 else 0
    else:
        features['Avg min between received tnx'] = 0
    
    if not txs.empty:
        time_diff = (txs['timeStamp'].max() - txs['timeStamp'].min()) / 60
        features['Time Diff between first and last (Mins)'] = time_diff
    else:
        features['Time Diff between first and last (Mins)'] = 0
    
    # Transaction counts
    features['Sent tnx'] = len(sent_txs)
    features['Received Tnx'] = len(received_txs)
    features['Number of Created Contracts'] = len(txs[txs['isError'] == '0'])
    features['Unique Received From Addresses'] = received_txs['from'].nunique()
    features['Unique Sent To Addresses'] = sent_txs['to'].nunique()
    
    # Value features - received
    if not received_txs.empty:
        features['min value received'] = received_txs['value'].min()
        features['max value received'] = received_txs['value'].max()
        features['avg val received'] = received_txs['value'].mean()
    else:
        features['min value received'] = 0
        features['max value received'] = 0
        features['avg val received'] = 0
    
    # Value features - sent
    if not sent_txs.empty:
        features['min val sent'] = sent_txs['value'].min()
        features['max val sent'] = sent_txs['value'].max()
        features['avg val sent'] = sent_txs['value'].mean()
    else:
        features['min val sent'] = 0
        features['max val sent'] = 0
        features['avg val sent'] = 0
    
    # Contract-related
    contract_txs = sent_txs[sent_txs['isError'] == '0']
    if not contract_txs.empty:
        features['min value sent to contract'] = contract_txs['value'].min()
        features['max val sent to contract'] = contract_txs['value'].max()
        features['avg value sent to contract'] = contract_txs['value'].mean()
    else:
        features['min value sent to contract'] = 0
        features['max val sent to contract'] = 0
        features['avg value sent to contract'] = 0
    
    # CRITICAL FIX: The training data scaler has extremely small std for these contract features
    # This causes scaling explosion. Cap to match training data ranges.
    contract_caps_strict = {
        'min value sent to contract': 100,  # Training max: 12000, but cap lower
        'max val sent to contract': 0.02,   # Training max: 0.02 (VERY small!)
        'avg value sent to contract': 0.05, # Training max: 0.046
    }
    
    for key, cap_value in contract_caps_strict.items():
        if key in features and features[key] > cap_value:
            features[key] = cap_value
    
    # Totals
    features['total transactions (including tnx to create contract'] = len(txs)
    features['total Ether sent'] = sent_txs['value'].sum()
    features['total ether received'] = received_txs['value'].sum()
    features['total ether sent contracts'] = contract_txs['value'].sum()
    features['total ether balance'] = features['total ether received'] - features['total Ether sent']
    
    # CRITICAL FIX: Cap extreme values to prevent scaling explosion
    # These caps match the training data value ranges to ensure compatibility with the scaler
    caps = {
        'max val sent': 1000,  # Cap at 1000 ETH
        'avg val sent': 100,
        'total Ether sent': 10000,
        'total ether received': 10000,
        'total ether sent contracts': 0.05,  # CRITICAL: Training scaler expects tiny values
    }
    
    for key, cap_value in caps.items():
        if key in features and features[key] > cap_value:
            print(f"[INFO] Capping {key}: {features[key]:.2f} -> {cap_value}")
            features[key] = cap_value
    
    # ERC20 features
    if not erc20_txs.empty:
        # CRITICAL FIX: Convert ERC20 token values from raw units to normalized decimals
        # ERC20 tokens have varying decimals (most common is 18, but can be 6, 8, etc.)
        # For consistency with training data, we normalize by 1e18 like ETH
        erc20_txs['value'] = pd.to_numeric(erc20_txs['value'], errors='coerce') / 1e18
        erc20_sent = erc20_txs[erc20_txs['from'].str.lower() == address.lower()]
        erc20_received = erc20_txs[erc20_txs['to'].str.lower() == address.lower()]
        
        features['Total ERC20 tnxs'] = len(erc20_txs)
        features['ERC20 total Ether received'] = erc20_received['value'].sum()
        features['ERC20 total ether sent'] = erc20_sent['value'].sum()
        features['ERC20 total Ether sent contract'] = erc20_sent['value'].sum()
        features['ERC20 uniq sent addr'] = erc20_sent['to'].nunique()
        features['ERC20 uniq rec addr'] = erc20_received['from'].nunique()
        features['ERC20 uniq sent addr.1'] = erc20_sent['to'].nunique()
        features['ERC20 uniq rec contract addr'] = erc20_received['contractAddress'].nunique()
        features['ERC20 min val rec'] = erc20_received['value'].min() if not erc20_received.empty else 0
        features['ERC20 max val rec'] = erc20_received['value'].max() if not erc20_received.empty else 0
        features['ERC20 avg val rec'] = erc20_received['value'].mean() if not erc20_received.empty else 0
        features['ERC20 min val sent'] = erc20_sent['value'].min() if not erc20_sent.empty else 0
        features['ERC20 max val sent'] = erc20_sent['value'].max() if not erc20_sent.empty else 0
        features['ERC20 avg val sent'] = erc20_sent['value'].mean() if not erc20_sent.empty else 0
        features['ERC20 uniq sent token name'] = erc20_sent['tokenName'].nunique()
        features['ERC20 uniq rec token name'] = erc20_received['tokenName'].nunique()
        
        # CRITICAL FIX: Cap extreme ERC20 values to match training data scaler ranges
        erc20_caps = {
            'ERC20 total Ether received': 1000000,  # Cap at 1M tokens
            'ERC20 total ether sent': 1000000,
            'ERC20 total Ether sent contract': 1000000,
            'ERC20 max val rec': 100000,
            'ERC20 max val sent': 100000,
            'ERC20 avg val rec': 10000,
            'ERC20 avg val sent': 10000,
            'ERC20 uniq sent addr': 500,           # Training max: 416000, but cap conservatively
            'ERC20 uniq rec addr': 500,            # Training max: 6582
            'ERC20 uniq sent addr.1': 500,         # Training max: 4293
            'ERC20 uniq rec contract addr': 3,     # Training max: 3 (VERY small!)
            'ERC20 uniq sent token name': 100,     # Training has huge values but cap conservatively
            'ERC20 uniq rec token name': 200,      # Training max: 213
        }
        
        for key, cap_value in erc20_caps.items():
            if key in features and features[key] > cap_value:
                print(f"[INFO] Capping {key}: {features[key]:.2f} -> {cap_value}")
                features[key] = cap_value
    else:
        # Zero out ERC20 features
        for key in ['Total ERC20 tnxs', 'ERC20 total Ether received', 'ERC20 total ether sent',
                    'ERC20 total Ether sent contract', 'ERC20 uniq sent addr', 'ERC20 uniq rec addr',
                    'ERC20 uniq sent addr.1', 'ERC20 uniq rec contract addr', 'ERC20 min val rec',
                    'ERC20 max val rec', 'ERC20 avg val rec', 'ERC20 min val sent', 'ERC20 max val sent',
                    'ERC20 avg val sent', 'ERC20 uniq sent token name', 'ERC20 uniq rec token name']:
            features[key] = 0
    
    # Validate feature dict matches training data columns
    try:
        validation_result = validate_feature_dict(features)
        # Handle 2-value return: (is_valid, missing)
        if len(validation_result) == 2:
            is_valid, missing = validation_result
            if not is_valid:
                print(f"[WARNING] Feature validation failed!")
                print(f"  Missing columns: {missing}")
        else:
            print(f"[WARNING] Unexpected validation result: {validation_result}")
    except Exception as e:
        print(f"[WARNING] Feature validation error: {e}")
    
    # CRITICAL FIX: Clip all features to be within 5σ of training data scaler
    # This prevents scaling explosion from extreme outliers
    features = clip_features_for_scaler(features)
    
    return features


def fetch_ethereum_wallet(address_or_tx_id):
    """
    Main function: fetch wallet data and compute features
    Returns: (features_dict, is_contract, red_flags, data_source)
    """
    # Check if input is a transaction hash
    if len(address_or_tx_id) == 66 and address_or_tx_id.startswith('0x'):
        print(f"Resolving transaction hash to address...")
        address = resolve_tx_to_address(address_or_tx_id)
        if not address:
            return None, False, ["Failed to resolve transaction hash"], "ERROR"
    else:
        address = address_or_tx_id
    
    print("\n" + "="*80)
    print("STEP 1: LIVE DATA FETCH - RAW API RESPONSE")
    print("="*80)
    print(f"Address: {address}")
    print(f"API: Etherscan V2")
    
    # Check for API key
    if not ETHERSCAN_API_KEY or ETHERSCAN_API_KEY == 'your_etherscan_api_key_here':
        print("[ERROR] No valid Etherscan API key found in .env file")
        return None, False, ["No Etherscan API key configured. Please add ETHERSCAN_API_KEY to .env file."], "ERROR"
    
    print(f"API Key (first 8 chars): {ETHERSCAN_API_KEY[:8]}...")
    
    # Real API calls
    txs = fetch_wallet_transactions(address)
    erc20_txs = fetch_erc20_transactions(address)
    
    if txs.empty and erc20_txs.empty:
        print(f"\n❌ CRITICAL: No transaction data returned!")
        print(f"This could mean:")
        print(f"  1. The address has never been used")
        print(f"  2. The API key has rate limits or is invalid")
        print(f"  3. The address format is invalid")
        print(f"  4. API is returning an error (check logs above)")
        return None, False, [
            "No transaction history found for this address.",
            "This address may have never been used, or the API request failed.",
            "Cannot generate risk score without transaction data."
        ], "NO_DATA"
    
    print(f"\n✅ Successfully fetched real data:")
    print(f"  - Normal transactions: {len(txs)}")
    print(f"  - ERC20 transactions: {len(erc20_txs)}")
    
    if not txs.empty:
        print(f"\nSample transaction data (first 3 rows):")
        print(txs[['from', 'to', 'value', 'timeStamp']].head(3).to_string())
    
    features = compute_features(address, txs, erc20_txs)
    
    print(f"\n✅ Computed {len(features)} features from real transaction data")
    
    # Check if contract
    is_contract, red_flags = check_contract_source(address)
    
    return features, is_contract, red_flags, "LIVE_API"


if __name__ == "__main__":
    # Test with a sample address
    test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    features, is_contract, red_flags = fetch_ethereum_wallet(test_address)
    
    if features:
        print("\n✅ Fetched features:")
        for k, v in list(features.items())[:10]:
            print(f"  {k}: {v}")
        print(f"\nIs contract: {is_contract}")
        print(f"Red flags: {red_flags}")
