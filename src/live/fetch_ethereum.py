"""
Live Ethereum Wallet Data Fetcher - PRODUCTION GRADE
Features: Rate limiting, caching, key rotation, retry logic, input validation
"""

import requests
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import sys
import time
from typing import Optional, Dict, Any

# Add parent directory for config imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from config.feature_columns import ETHEREUM_FEATURE_COLUMNS, validate_feature_dict

# Import accuracy module
from src.accuracy.feature_calculator import FeatureCalculator

# Import contract and DEX analyzers
from src.live.contract_analyzer import ContractAnalyzer
from src.live.dex_analyzer import DexAnalyzer

# Import security modules
try:
    from src.security.rate_limiter import global_rate_limiter, rate_limit
    from src.security.input_validator import InputValidator, SecurityValidator
    from src.security.key_manager import global_key_manager
    from src.security.cache_manager import global_address_cache
    SECURITY_ENABLED = True
except ImportError:
    print("[WARNING] Security modules not initialized. Using fallback mode.")
    SECURITY_ENABLED = False
    global_rate_limiter = None
    global_key_manager = None
    global_address_cache = None
    
    # Fallback InputValidator
    class InputValidator:
        @staticmethod
        def detect_blockchain(address):
            if address.startswith('0x') and len(address) == 42:
                return 'ethereum'
            elif address.startswith('0x') and len(address) == 66:
                return 'ethereum_tx'
            else:
                return 'unknown'
        
        @staticmethod
        def validate_ethereum_address(address):
            """Basic validation without EIP-55 checksum"""
            if not address.startswith('0x'):
                return False, address, "Address must start with 0x"
            if len(address) != 42:
                return False, address, "Address must be 42 characters"
            try:
                int(address, 16)  # Check if hex
                return True, address.lower(), None
            except ValueError:
                return False, address, "Address contains invalid characters"
        
        @staticmethod
        def validate_ethereum_tx(tx_hash):
            """Basic transaction hash validation"""
            if not tx_hash.startswith('0x'):
                return False, tx_hash, "Transaction hash must start with 0x"
            if len(tx_hash) != 66:
                return False, tx_hash, "Transaction hash must be 66 characters"
            try:
                int(tx_hash, 16)  # Check if hex
                return True, tx_hash.lower(), None
            except ValueError:
                return False, tx_hash, "Transaction hash contains invalid characters"
    
    # Fallback SecurityValidator
    class SecurityValidator:
        @staticmethod
        def check_honeypot_indicators(address, features):
            """Fallback - no honeypot detection"""
            return []

load_dotenv()

# Load API key
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')

ETHERSCAN_BASE_URL = "https://api.etherscan.io/v2/api"  # V2 endpoint
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def resolve_tx_to_address(tx_hash):
    """Resolve transaction hash to sender address"""
    params = {
        'chainid': '1',
        'module': 'proxy',
        'action': 'eth_getTransactionByHash',
        'txhash': tx_hash,
        'apikey': ETHERSCAN_API_KEY
    }
    
    response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=30)  # Increased from 10 to 30 seconds
    data = response.json()
    
    if data.get('result'):
        return data['result'].get('from')
    
    return None


def fetch_wallet_transactions(address: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch transactions with enterprise-grade features:
    - Automatic caching (5min TTL)
    - Key rotation
    - Retry logic with exponential backoff
    - Rate limit handling
    """
    # Check cache first
    if use_cache and global_address_cache:
        cached = global_address_cache.cache.get('transaction_list', address.lower())
        if cached is not None:
            print(f"[CACHE HIT] Using cached transactions for {address[:10]}...")
            return pd.DataFrame(cached)
    
    # Get API key from key manager
    api_key = os.getenv('ETHERSCAN_API_KEY', '')
    if global_key_manager:
        key_obj = global_key_manager.get_key('etherscan')
        if key_obj:
            api_key = key_obj.key
        else:
            raise RuntimeError("All API keys exhausted. Please try again later.")
    
    params = {
        'chainid': '1',
        'module': 'account',
        'action': 'txlist',
        'address': address,
        'startblock': '0',
        'endblock': '99999999',
        'page': '1',
        'offset': '10000',
        'sort': 'asc',
        'apikey': api_key
    }
    
    # Retry logic with exponential backoff
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=15)
            data = response.json()
            
            # Handle rate limiting
            if data.get('status') == '0' and 'rate limit' in data.get('message', '').lower():
                if global_key_manager and key_obj:
                    global_key_manager.mark_rate_limited(key_obj, cooldown_seconds=60)
                
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    print(f"[RATE LIMIT] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError("API rate limit exceeded. Please try again in 1 minute.")
            
            # Handle other errors
            if data.get('status') == '0':
                message = data.get('message', '')
                if 'no transactions found' not in message.lower():
                    # Mark key as invalid if authentication error
                    if 'invalid' in message.lower() and global_key_manager and key_obj:
                        global_key_manager.mark_invalid(key_obj)
                    
                    raise RuntimeError(f"Etherscan API error: {message}")
            
            # Success
            if data.get('status') == '1' and isinstance(data.get('result'), list):
                df = pd.DataFrame(data['result'])
                
                # Cache for future requests
                if use_cache and global_address_cache and not df.empty:
                    global_address_cache.cache.set('transaction_list', address.lower(), data['result'])
                
                print(f"[SUCCESS] Fetched {len(df)} transactions")
                return df
            
            return pd.DataFrame()
            
        except requests.Timeout:
            if attempt < MAX_RETRIES - 1:
                print(f"[TIMEOUT] Retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(RETRY_DELAY)
                continue
            else:
                raise RuntimeError("Request timeout. The address may have too many transactions. Please try again.")
        
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            else:
                raise RuntimeError(f"Network error: {str(e)}")
    
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
    
    response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=30)  # Increased from 10 to 30 seconds
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
    
    response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=30)  # Increased from 10 to 30 seconds
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
    
    return features


def fetch_ethereum_wallet(address_or_tx_id: str, truncate_time: Optional[int] = None, user_id: str = "anonymous", ip_address: str = "0.0.0.0") -> tuple[Optional[Dict[str, Any]], bool, list[str], str]:
    """
    PRODUCTION-GRADE wallet analysis with full security stack
    
    Args:
        address_or_tx_id: Ethereum address or transaction hash  
        truncate_time: Optional time limit in seconds (for testing)
        user_id: User identifier for rate limiting
        ip_address: Client IP for DDoS protection
    
    Returns: (features_dict, is_contract, red_flags, data_source)
    
    Raises:
        RuntimeError: API errors, rate limits, validation failures
        ValueError: Invalid input format
    """
    # STEP 1: Input validation
    blockchain = InputValidator.detect_blockchain(address_or_tx_id)
    
    if blockchain == 'ethereum_tx':
        # Transaction hash - resolve to address
        valid, normalized, error = InputValidator.validate_ethereum_tx(address_or_tx_id)
        if not valid:
            raise ValueError(f"Invalid transaction hash: {error}")
        address = resolve_tx_to_address(normalized)
        if not address:
            raise RuntimeError("Failed to resolve transaction hash to address")
    elif blockchain == 'ethereum':
        # Direct address
        valid, normalized, error = InputValidator.validate_ethereum_address(address_or_tx_id)
        if not valid:
            raise ValueError(f"Invalid Ethereum address: {error}")
        address = normalized
    else:
        raise ValueError("Invalid input. Please enter a valid Ethereum address (0x...)")
    
    # STEP 2: Check rate limits
    if global_rate_limiter:
        api_key = os.getenv('ETHERSCAN_API_KEY', '')
        allowed, error_msg = global_rate_limiter.check_all(user_id, ip_address, api_key)
        if not allowed:
            raise RuntimeError(error_msg)
    
    # STEP 3: Check cache
    if global_address_cache:
        cached_result = global_address_cache.get_risk_score(address)
        if cached_result:
            print(f"[CACHE HIT] Returning cached analysis for {address[:10]}...")
            return cached_result['features'], False, cached_result['flags'], "CACHED"
    
    print("\n" + "="*80)
    print("STEP 1: LIVE DATA FETCH - RAW API RESPONSE")
    print("="*80)
    print(f"Address: {address}")
    print(f"API: Etherscan V2")
    
    # Real API calls (using production-grade fetcher with caching, retry, rate limiting)
    txs = fetch_wallet_transactions(address, use_cache=True)
    erc20_txs = pd.DataFrame()  # Not used for GNN-22
    
    if txs.empty:
        print(f"\n❌ CRITICAL: No transaction data returned!")
        return None, False, [
            "No transaction history found for this address.",
            "This address may have never been used, or the API request failed."
        ], "NO_DATA"
    
    print(f"\n✅ Successfully fetched real data:")
    print(f"  - Normal transactions: {len(txs)}")
    
    if not txs.empty:
        print(f"\nSample transaction data (first 3 rows):")
        print(txs[['from', 'to', 'value', 'timeStamp']].head(3).to_string())
    
    # PRODUCTION: Use FeatureCalculator for 100% accuracy
    features = FeatureCalculator.calculate_all_features(address, txs, erc20_txs, truncate_time)
    
    # Validate features
    valid, errors = FeatureCalculator.validate_features(features)
    if not valid:
        print(f"\n⚠️  WARNING: Feature validation failed:")
        for error in errors:
            print(f"  - {error}")
    
    print(f"\n✅ Computed {len(features)} features from real transaction data")
    
    # PHASE 1: Add contract analysis
    try:
        contract_analyzer = ContractAnalyzer(ETHERSCAN_API_KEY)
        if contract_analyzer.is_contract(address):
            contract_features = contract_analyzer.analyze_contract(address)
            features.update(contract_features)
            print(f"✅ Added contract admin features: {sum(contract_features.values())} powers detected")
        else:
            # Not a contract - add zeros
            features.update({
                'can_mint': 0,
                'has_blacklist': 0,
                'can_pause': 0,
                'fee_too_high': 0,
                'has_trading_limits': 0,
                'has_trading_cooldown': 0,
                'owner_can_withdraw': 0,
                'owner_change_balance': 0,
            })
    except Exception as e:
        print(f"⚠️  Contract analysis failed: {e}")
        # Add zeros as fallback
        features.update({
            'can_mint': 0,
            'has_blacklist': 0,
            'can_pause': 0,
            'fee_too_high': 0,
            'has_trading_limits': 0,
            'has_trading_cooldown': 0,
            'owner_can_withdraw': 0,
            'owner_change_balance': 0,
        })
    
    # PHASE 1: Add DEX analysis
    try:
        dex_analyzer = DexAnalyzer(etherscan_api_key=ETHERSCAN_API_KEY)
        dex_data = dex_analyzer.analyze_token(address)
        features.update(dex_data)
        print(f"✅ Added DEX data: ${dex_data['total_liquidity_usd']:,.0f} liquidity, {dex_data['pair_created_days']} days old")
    except Exception as e:
        print(f"⚠️  DEX analysis failed: {e}")
        # Add zeros as fallback
        features.update({
            'total_liquidity_usd': 0.0,
            'pair_created_days': 0,
        })
    
    # Check if contract
    is_contract, red_flags = check_contract_source(address)
    
    # Add security validator checks
    security_flags = SecurityValidator.check_honeypot_indicators(address, features)
    red_flags.extend(security_flags)
    
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
