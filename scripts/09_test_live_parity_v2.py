"""
Test live feature parity on 3 wallets using Etherscan API V2
"""

import requests
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

# 3 test wallets
test_addresses = [
    '0x490d29b8669823e12eb5f72d53c27ebe7f952ab4',  # Fraud
    '0xa68b5746deaf18481a4ba57b61b69872381c9535',  # Legit
    '0x85ef23bf9503300df9273725166503a1fc18c1b7',  # Legit
]

test_df = pd.read_csv('data/splits/ethereum/test.csv')

print("="*80)
print("LIVE FEATURE PARITY TEST (3 WALLETS, 22 NON-ERC20 FEATURES)")
print("="*80)

# Fetch using V2 API
def fetch_etherscan_v2(address):
    """Fetch using V2 API with chainid"""
    base_url = "https://api.etherscan.io/v2/api"
    
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
        'apikey': ETHERSCAN_API_KEY
    }
    
    try:
        resp = requests.get(base_url, params=params, timeout=10)
        data = resp.json()
        
        if data.get('status') == '1':
            return data.get('result', []), None
        else:
            return [], data.get('message', 'Unknown error')
    except Exception as e:
        return [], str(e)

print("\n[1/2] Fetching live data...")
live_data = {}
for addr in test_addresses:
    print(f"  {addr[:10]}...", end=' ')
    txs, error = fetch_etherscan_v2(addr)
    if error:
        print(f"ERROR: {error}")
        live_data[addr] = None
    else:
        print(f"{len(txs)} transactions")
        live_data[addr] = txs
    
    import time
    time.sleep(0.3)  # Rate limiting

# Compute features from live data
def compute_features(address, txs):
    """Compute basic features from transaction list"""
    if not txs:
        return None
    
    addr_lower = address.lower()
    
    # Separate sent/received
    sent = [tx for tx in txs if tx.get('from', '').lower() == addr_lower]
    recv = [tx for tx in txs if tx.get('to', '').lower() == addr_lower and tx.get('from', '').lower() != addr_lower]
    
    # Values in ETH
    sent_values = []
    recv_values = []
    
    for tx in sent:
        try:
            val = float(tx.get('value', '0')) / 1e18
            sent_values.append(val)
        except:
            pass
    
    for tx in recv:
        try:
            val = float(tx.get('value', '0')) / 1e18
            recv_values.append(val)
        except:
            pass
    
    features = {
        'Sent tnx': len(sent),
        'Received Tnx': len(recv),
        'total transactions (including tnx to create contract': len(txs),
        'min val sent': min(sent_values) if sent_values else 0,
        'max val sent': max(sent_values) if sent_values else 0,
        'avg val sent': np.mean(sent_values) if sent_values else 0,
        'min value received': min(recv_values) if recv_values else 0,
        'max value received': max(recv_values) if recv_values else 0,
        'avg val received': np.mean(recv_values) if recv_values else 0,
        'total Ether sent': sum(sent_values),
        'total ether received': sum(recv_values),
        'total ether balance': sum(recv_values) - sum(sent_values),
    }
    
    return features

print("\n[2/2] Computing features and comparing to Kaggle...")

comparison_table = []

for addr in test_addresses:
    if live_data[addr] is None:
        print(f"\n{addr}: SKIPPED (fetch failed)")
        continue
    
    live_feats = compute_features(addr, live_data[addr])
    kaggle_row = test_df[test_df['Address'] == addr].iloc[0]
    
    print(f"\n{addr}:")
    print(f"  {'Feature':<35} {'Kaggle':<12} {'Live':<12} {'Ratio':<8}")
    print(f"  {'-'*70}")
    
    # Focus on the 3 key features
    key_features = ['Sent tnx', 'Received Tnx', 'total transactions (including tnx to create contract']
    
    for feat in key_features:
        kaggle_val = kaggle_row[feat]
        live_val = live_feats[feat]
        
        if kaggle_val == 0 and live_val == 0:
            ratio = 1.0
        elif kaggle_val == 0:
            ratio = 999.0
        elif live_val == 0:
            ratio = 0.0
        else:
            ratio = live_val / kaggle_val
        
        comparison_table.append({
            'address': addr[:10],
            'feature': feat,
            'kaggle': kaggle_val,
            'live': live_val,
            'ratio': ratio
        })
        
        print(f"  {feat:<35} {kaggle_val:<12.1f} {live_val:<12.1f} {ratio:<8.3f}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

comp_df = pd.DataFrame(comparison_table)
if len(comp_df) > 0:
    exact_match = (comp_df['ratio'] == 1.0).sum()
    close_match = ((comp_df['ratio'] > 0.9) & (comp_df['ratio'] < 1.1)).sum()
    print(f"Exact matches (ratio=1.0): {exact_match}/{len(comp_df)}")
    print(f"Close matches (0.9-1.1): {close_match}/{len(comp_df)}")
    print(f"Median ratio: {comp_df['ratio'].median():.3f}")
else:
    print("No valid comparisons")

print("="*80)
