"""
Live Solana Pool Data Fetcher
Fetches liquidity pool history using Helius RPC API and computes rug-pull detection features

Helius API: https://docs.helius.dev/
Required: HELIUS_API_KEY in .env file
"""

import requests
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from datetime import datetime
import time

load_dotenv()

HELIUS_API_KEY = os.getenv('HELIUS_API_KEY', '')
HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"


def fetch_address_transactions(address, limit=1000):
    """
    Fetch transaction history for a Solana address using Helius RPC
    Returns: list of parsed transactions
    """
    try:
        # Use Helius enhanced transaction API
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                address,
                {"limit": limit}
            ]
        }
        
        response = requests.post(HELIUS_RPC_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                return result['result']
        
        return []
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return []


def analyze_liquidity_events(transactions):
    """
    Parse transactions to extract liquidity add/remove events
    
    For Solana liquidity pools, we look for:
    - Token transfers that increase pool balance (adds)
    - Token transfers that decrease pool balance (removes)
    
    Note: This is a simplified heuristic. Real implementation would:
    - Parse Raydium/Orca/Jupiter program instructions
    - Identify specific liquidity pool events
    - Track token mint addresses
    """
    liquidity_adds = []
    liquidity_removes = []
    
    for tx in transactions:
        signature = tx.get('signature', '')
        timestamp = tx.get('blockTime', 0)
        
        # In a full implementation, we'd fetch each transaction detail
        # and parse the instructions to identify liquidity events
        # For now, we use a heuristic based on transaction metadata
        
        err = tx.get('err')
        
        # Successful transactions only
        if err is None:
            # This is a placeholder - real implementation would:
            # 1. Fetch full transaction with getParsedTransaction
            # 2. Parse token transfers and program instructions
            # 3. Identify liquidity add/remove instructions
            pass
    
    return liquidity_adds, liquidity_removes


def compute_features_from_events(liquidity_adds, liquidity_removes, first_timestamp, last_timestamp):
    """
    Compute 7 features from liquidity events
    """
    features = {}
    
    # Count events
    num_adds = len(liquidity_adds)
    num_removes = len(liquidity_removes)
    
    # Sum amounts
    total_added = sum([event.get('amount', 0) for event in liquidity_adds])
    total_removed = sum([event.get('amount', 0) for event in liquidity_removes])
    
    features['NUM_LIQUIDITY_ADDS'] = num_adds
    features['NUM_LIQUIDITY_REMOVES'] = num_removes
    features['TOTAL_ADDED_LIQUIDITY'] = total_added
    features['TOTAL_REMOVED_LIQUIDITY'] = total_removed
    
    # REMOVE_RATIO (capped at 10)
    if total_added > 0:
        features['REMOVE_RATIO'] = min(total_removed / total_added, 10.0)
    else:
        features['REMOVE_RATIO'] = 0.0
    
    # ADD_TO_REMOVE_RATIO
    if num_removes > 0:
        features['ADD_TO_REMOVE_RATIO'] = num_adds / num_removes
    else:
        features['ADD_TO_REMOVE_RATIO'] = float(num_adds) if num_adds > 0 else 0.0
    
    # POOL_LIFETIME_HOURS
    if first_timestamp and last_timestamp:
        lifetime_seconds = last_timestamp - first_timestamp
        features['POOL_LIFETIME_HOURS'] = lifetime_seconds / 3600
    else:
        features['POOL_LIFETIME_HOURS'] = 0.0
    
    return features


def fetch_solana_pool(pool_address):
    """
    Main function: fetch pool data and compute features using Helius API
    Returns: (features_dict, red_flags, data_source)
    """
    print(f"\n{'='*60}")
    print(f"Fetching Solana pool data: {pool_address}")
    print(f"Using: Helius RPC API")
    print(f"{'='*60}")
    
    # Check for API key
    if not HELIUS_API_KEY:
        print("[ERROR] Missing Helius API key")
        return None, [
            "No Helius API key configured.",
            "Please add HELIUS_API_KEY to .env file.",
            "Get free key at: https://www.helius.dev/"
        ], "ERROR"
    
    print(f"[INFO] API Key found (first 10 chars): {HELIUS_API_KEY[:10]}...")
    
    # Fetch transactions for this pool address
    print(f"[INFO] Fetching transaction history...")
    transactions = fetch_address_transactions(pool_address, limit=1000)
    
    if not transactions:
        print(f"[WARNING] No transactions found for this address")
        return None, [
            "No transaction history found for this address.",
            "This may not be a valid liquidity pool address,",
            "or the pool has no recorded transactions."
        ], "NO_DATA"
    
    print(f"[INFO] Found {len(transactions)} transactions")
    
    # Extract timestamps
    timestamps = [tx.get('blockTime', 0) for tx in transactions if tx.get('blockTime')]
    if timestamps:
        first_timestamp = min(timestamps)
        last_timestamp = max(timestamps)
        first_dt = datetime.fromtimestamp(first_timestamp)
        last_dt = datetime.fromtimestamp(last_timestamp)
        print(f"[INFO] Pool activity: {first_dt.strftime('%Y-%m-%d')} to {last_dt.strftime('%Y-%m-%d')}")
    else:
        first_timestamp = None
        last_timestamp = None
    
    # Parse liquidity events
    print(f"[INFO] Parsing liquidity events...")
    liquidity_adds, liquidity_removes = analyze_liquidity_events(transactions)
    
    # IMPORTANT: The current implementation cannot fully parse liquidity events
    # because it requires detailed transaction parsing with program-specific logic
    # This is a limitation of the live API implementation
    
    print(f"\n[WARNING] ⚠️  LIVE API LIMITATION ⚠️")
    print(f"[WARNING] Full liquidity event parsing requires:")
    print(f"[WARNING]   1. Fetching each transaction's full details")
    print(f"[WARNING]   2. Parsing Raydium/Orca/Jupiter program instructions")
    print(f"[WARNING]   3. Identifying specific liquidity pool events")
    print(f"[WARNING] This is not fully implemented yet.")
    print(f"\n[INFO] Using simplified transaction count heuristic...")
    
    # Fallback: use simple heuristics based on transaction count
    # This is NOT accurate but demonstrates the API connection
    features = {
        'NUM_LIQUIDITY_ADDS': len(transactions) // 10,  # Heuristic
        'NUM_LIQUIDITY_REMOVES': len(transactions) // 20,  # Heuristic
        'TOTAL_ADDED_LIQUIDITY': len(transactions) * 100,  # Placeholder
        'TOTAL_REMOVED_LIQUIDITY': len(transactions) * 30,  # Placeholder
        'POOL_LIFETIME_HOURS': (last_timestamp - first_timestamp) / 3600 if timestamps else 0,
        'REMOVE_RATIO': 0.3,  # Placeholder
        'ADD_TO_REMOVE_RATIO': 2.0,  # Placeholder
    }
    
    print(f"\n[INFO] Computed features (using heuristics):")
    for k, v in features.items():
        print(f"  {k}: {v}")
    
    # Check for red flags (using heuristic features)
    red_flags = []
    
    if features['REMOVE_RATIO'] >= 0.85:
        red_flags.append("High liquidity removal ratio (≥85%)")
    
    if len(transactions) == 0 or (timestamps and (time.time() - last_timestamp) > 30*24*3600):
        red_flags.append("Pool appears inactive (no recent transactions)")
    
    if features['NUM_LIQUIDITY_ADDS'] <= 3:
        red_flags.append("Very few liquidity additions (≤3)")
    
    if len(red_flags) >= 2:
        red_flags.append("⚠️  WARNING: Matches multiple rug-pull indicators")
    
    # Add disclaimer
    red_flags.insert(0, "⚠️  DEMO MODE: Using transaction count heuristics (not full liquidity parsing)")
    
    return features, red_flags, "LIVE_API_PARTIAL"


if __name__ == "__main__":
    # Test with a known Solana address
    # This is a Raydium USDC-SOL pool address
    test_pool = "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"
    
    print("="*70)
    print("TESTING SOLANA LIVE API (HELIUS)")
    print("="*70)
    
    features, red_flags, source = fetch_solana_pool(test_pool)
    
    if features:
        print(f"\n{'='*70}")
        print("✅ RESULT")
        print(f"{'='*70}")
        print(f"Data source: {source}")
        print(f"\nFeatures:")
        for k, v in features.items():
            print(f"  {k}: {v}")
        print(f"\nRed flags ({len(red_flags)}):")
        for flag in red_flags:
            print(f"  - {flag}")
    else:
        print(f"\n{'='*70}")
        print("❌ FAILED TO FETCH DATA")
        print(f"{'='*70}")
        print(f"Red flags:")
        for flag in red_flags:
            print(f"  - {flag}")
