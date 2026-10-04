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
    params = {
        'chainid': '1',
        'module': 'proxy',
        'action': 'eth_getTransactionByHash',
        'txhash': tx_hash,
        'apikey': ETHERSCAN_API_KEY
    }
    
    response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10)
    data = response.json()
    
    if data.get('result'):
        return data['result'].get('from')
    
    return None


def fetch_wallet_transactions(address):
    """Fetch normal transactions for wallet using Etherscan V2 API"""
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
    
    response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10)
    data = response.json()
    
    # Raise if API returns error (unless it's "No transactions found")
    if data.get('status') == '0':
        message = data.get('message', '')
        if 'no transactions found' not in message.lower():
            raise RuntimeError(f"Etherscan API error: {message} (result: {data.get('result', 'N/A')})")
    
    if data.get('status') == '1' and isinstance(data.get('result'), list):
        print(f"[SUCCESS] Fetched {len(data['result'])} transactions")
        return pd.DataFrame(data['result'])
    
    return pd.DataFrame()


def fetch_erc20_transactions(address):
    """Fetch ERC20 token transactions using V2 API"""
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
    
    # Raise if API returns error (unless it's "No transactions found")
    if data.get('status') == '0':
        message = data.get('message', '')
        if 'no transactions found' not in message.lower():
            raise RuntimeError(f"Etherscan API error: {message} (result: {data.get('result', 'N/A')})")
    
    if data.get('status') == '1' and isinstance(data.get('result'), list):
        print(f"[SUCCESS] Fetched {len(data['result'])} ERC20 transactions")
        return pd.DataFrame(data['result'])
    
    return pd.DataFrame()


def check_contract_source(address):
    """Check if address is a contract and analyze source code"""
    params = {
        'chainid': '1',
        'module': 'contract',
        'action': 'getsourcecode',
        'address': address,
        'apikey': ETHERSCAN_API_KEY
    }
    
    response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10)
    data = response.json()
    
    # Raise if API returns error
    if data.get('status') == '0':
        message = data.get('message', '')
        raise RuntimeError(f"Etherscan API error: {message}")
    
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


def compute_features(address, txs, erc20_txs, truncate_time=None):
    """
    Compute the SAME 22 non-ERC20 features used in ethereum_clean.csv
    
    Args:
        address: Wallet address
        txs: DataFrame of transactions
        erc20_txs: DataFrame of ERC20 transactions (unused for 22 features)
        truncate_time: Optional timestamp limit (exclude txs after first_tx + this duration in seconds)
    """
    features = {}
    
    if txs.empty:
        # Return zero features
        return {f'feature_{i}': 0.0 for i in range(22)}
    
    # Convert to numeric
    txs['value'] = pd.to_numeric(txs['value'], errors='coerce') / 1e18  # Wei to ETH
    txs['timeStamp'] = pd.to_numeric(txs['timeStamp'], errors='coerce')
    
    # Apply truncation if specified (for parity testing on wallets with new activity)
    if truncate_time is not None:
        first_tx_time = txs['timeStamp'].min()
        txs = txs[txs['timeStamp'] <= first_tx_time + truncate_time].copy()
    
    # Separate sent vs received (exclude self-transfers)
    addr_lower = address.lower()
    sent_txs = txs[txs['from'].str.lower() == addr_lower].copy()
    received_txs = txs[(txs['to'].str.lower() == addr_lower) & (txs['from'].str.lower() != addr_lower)].copy()
    
    # FIXED: Time-based features - average of the time differences between consecutive transactions
    if len(sent_txs) > 1:
        sent_sorted = sent_txs.sort_values('timeStamp')
        sent_diffs = sent_sorted['timeStamp'].diff().dropna() / 60  # minutes
        features['Avg min between sent tnx'] = sent_diffs.mean()
    else:
        features['Avg min between sent tnx'] = 0
    
    if len(received_txs) > 1:
        recv_sorted = received_txs.sort_values('timeStamp')
        recv_diffs = recv_sorted['timeStamp'].diff().dropna() / 60
        features['Avg min between received tnx'] = recv_diffs.mean()
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
    
    # FIXED: Number of Created Contracts - count only txs with non-empty contractAddress
    created_contracts = 0
    if 'contractAddress' in txs.columns:
        # Contract is created when contractAddress is not empty/null
        created_contracts = txs['contractAddress'].notna().sum()
        # Also filter out empty strings
        if created_contracts > 0:
            created_contracts = (txs['contractAddress'].fillna('') != '').sum()
    features['Number of Created Contracts'] = created_contracts
    
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
    
    # FIXED: Contract-related features
    # Definition: transactions TO contracts (recipient is a contract, indicated by non-empty input field)
    # In Etherscan API: input != '0x' means the recipient is a contract
    contract_txs = sent_txs[(sent_txs['input'] != '0x') & (sent_txs['input'].notna())].copy() if 'input' in sent_txs.columns else pd.DataFrame()
    
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
    # FIXED: Total ether sent to contracts (sum of contract_txs values)
    features['total ether sent contracts'] = contract_txs['value'].sum() if not contract_txs.empty else 0
    features['total ether balance'] = features['total ether received'] - features['total Ether sent']
    
    # Return only the 22 non-ERC20 features (no ERC20 features needed for GNN-22)
    return features


def compute_features_38(address, txs, erc20_txs, truncate_time=None):
    """
    Legacy 38-feature version (includes ERC20) - not used in production
    """
    # Start with 22 features
    features = compute_features(address, txs, erc20_txs, truncate_time)
    
    # Add ERC20 features
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
    
    else:
        # Zero out ERC20 features
        for key in ['Total ERC20 tnxs', 'ERC20 total Ether received', 'ERC20 total ether sent',
                    'ERC20 total Ether sent contract', 'ERC20 uniq sent addr', 'ERC20 uniq rec addr',
                    'ERC20 uniq sent addr.1', 'ERC20 uniq rec contract addr', 'ERC20 min val rec',
                    'ERC20 max val rec', 'ERC20 avg val rec', 'ERC20 min val sent', 'ERC20 max val sent',
                    'ERC20 avg val sent', 'ERC20 uniq sent token name', 'ERC20 uniq rec token name']:
            features[key] = 0
    
    return features


def fetch_ethereum_wallet(address_or_tx_id, truncate_time=None):
    """
    Main function: fetch wallet data and compute 22 non-ERC20 features
    
    Args:
        address_or_tx_id: Ethereum address or transaction hash
        truncate_time: Optional time limit in seconds (for parity testing)
    
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
    
    # Real API calls (no ERC20 needed for GNN-22)
    txs = fetch_wallet_transactions(address)
    erc20_txs = pd.DataFrame()  # Not used for GNN-22
    
    if txs.empty:
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
    
    if not txs.empty:
        print(f"\nSample transaction data (first 3 rows):")
        print(txs[['from', 'to', 'value', 'timeStamp']].head(3).to_string())
    
    features = compute_features(address, txs, erc20_txs, truncate_time)
    
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
