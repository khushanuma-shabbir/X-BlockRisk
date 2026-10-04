"""
Parity test with FIXED features and truncation for wallets with new activity
"""

import pandas as pd
import numpy as np
import requests
import os
from dotenv import load_dotenv

load_dotenv()
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

test_addresses = [
    '0x490d29b8669823e12eb5f72d53c27ebe7f952ab4',  # Fraud, 10 tx, no new activity
    '0xa68b5746deaf18481a4ba57b61b69872381c9535',  # Legit, 2 tx, HAS new activity
    '0x85ef23bf9503300df9273725166503a1fc18c1b7',  # Legit, 5 tx, no new activity
    '0x1b133fde5bff441c6afce6aaddd9fdcdf980735e',  # Legit, 12 tx, HAS new activity
]

test_df = pd.read_csv('data/splits/ethereum/test.csv')

non_erc20_features = [
    'Avg min between sent tnx', 'Avg min between received tnx',
    'Time Diff between first and last (Mins)', 'Sent tnx', 'Received Tnx',
    'Number of Created Contracts', 'Unique Received From Addresses',
    'Unique Sent To Addresses', 'min value received', 'max value received',
    'avg val received', 'min val sent', 'max val sent', 'avg val sent',
    'min value sent to contract', 'max val sent to contract',
    'avg value sent to contract', 'total transactions (including tnx to create contract',
    'total Ether sent', 'total ether received', 'total ether sent contracts',
    'total ether balance'
]

print("="*80)
print("PARITY TEST - FIXED FEATURES + TRUNCATION")
print("="*80)

def fetch_v2(address):
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
    
    response = requests.get("https://api.etherscan.io/v2/api", params=params, timeout=10)
    data = response.json()
    
    if data.get('status') == '0':
        if 'no transactions found' not in data.get('message', '').lower():
            raise RuntimeError(f"API error: {data.get('message')}")
    
    if data.get('status') == '1' and isinstance(data.get('result'), list):
        return data['result']
    return []

def compute_fixed(address, txs, truncate_time=None):
    """Compute with FIXED definitions"""
    if not txs:
        return {feat: 0.0 for feat in non_erc20_features}
    
    df = pd.DataFrame(txs)
    df['value'] = pd.to_numeric(df['value'], errors='coerce') / 1e18
    df['timeStamp'] = pd.to_numeric(df['timeStamp'], errors='coerce')
    df['from'] = df['from'].str.lower()
    df['to'] = df['to'].str.lower()
    
    # Apply truncation
    if truncate_time is not None:
        first_tx = df['timeStamp'].min()
        df = df[df['timeStamp'] <= first_tx + truncate_time].copy()
    
    addr_lower = address.lower()
    sent = df[df['from'] == addr_lower].copy()
    recv = df[(df['to'] == addr_lower) & (df['from'] != addr_lower)].copy()
    
    features = {}
    
    # FIXED: Time averages - total_time / (n-1)
    if len(sent) > 1:
        sent_sorted = sent.sort_values('timeStamp')
        total_time = (sent_sorted['timeStamp'].iloc[-1] - sent_sorted['timeStamp'].iloc[0]) / 60
        features['Avg min between sent tnx'] = total_time / (len(sent) - 1)
    else:
        features['Avg min between sent tnx'] = 0.0
    
    if len(recv) > 1:
        recv_sorted = recv.sort_values('timeStamp')
        total_time = (recv_sorted['timeStamp'].iloc[-1] - recv_sorted['timeStamp'].iloc[0]) / 60
        features['Avg min between received tnx'] = total_time / (len(recv) - 1)
    else:
        features['Avg min between received tnx'] = 0.0
    
    features['Time Diff between first and last (Mins)'] = (df['timeStamp'].max() - df['timeStamp'].min()) / 60
    
    # Counts
    features['Sent tnx'] = len(sent)
    features['Received Tnx'] = len(recv)
    
    # FIXED: Number of Created Contracts - only non-empty contractAddress
    created = 0
    if 'contractAddress' in df.columns:
        created = (df['contractAddress'].fillna('') != '').sum()
    features['Number of Created Contracts'] = created
    
    features['Unique Received From Addresses'] = recv['from'].nunique()
    features['Unique Sent To Addresses'] = sent['to'].nunique()
    
    # Values
    features['min value received'] = recv['value'].min() if len(recv) > 0 else 0.0
    features['max value received'] = recv['value'].max() if len(recv) > 0 else 0.0
    features['avg val received'] = recv['value'].mean() if len(recv) > 0 else 0.0
    features['min val sent'] = sent['value'].min() if len(sent) > 0 else 0.0
    features['max val sent'] = sent['value'].max() if len(sent) > 0 else 0.0
    features['avg val sent'] = sent['value'].mean() if len(sent) > 0 else 0.0
    
    # FIXED: Contract transactions - input != '0x'
    contract_txs = sent[(sent['input'] != '0x') & (sent['input'].notna())].copy() if 'input' in sent.columns else pd.DataFrame()
    features['min value sent to contract'] = contract_txs['value'].min() if len(contract_txs) > 0 else 0.0
    features['max val sent to contract'] = contract_txs['value'].max() if len(contract_txs) > 0 else 0.0
    features['avg value sent to contract'] = contract_txs['value'].mean() if len(contract_txs) > 0 else 0.0
    
    # Totals
    features['total transactions (including tnx to create contract'] = len(df)
    features['total Ether sent'] = sent['value'].sum()
    features['total ether received'] = recv['value'].sum()
    features['total ether sent contracts'] = contract_txs['value'].sum() if len(contract_txs) > 0 else 0.0
    features['total ether balance'] = features['total ether received'] - features['total Ether sent']
    
    return features

print("\n[1/2] Fetching live data...")
live_data = {}
for addr in test_addresses:
    print(f"  {addr[:10]}...", end=' ')
    txs = fetch_v2(addr)
    live_data[addr] = txs
    print(f"{len(txs)} transactions")
    import time
    time.sleep(0.3)

print("\n[2/2] Computing with truncation...")

results = []
for addr in test_addresses:
    kaggle_row = test_df[test_df['Address'] == addr].iloc[0]
    
    # Determine truncation
    time_diff_kaggle = kaggle_row['Time Diff between first and last (Mins)'] * 60  # seconds
    truncate = time_diff_kaggle if time_diff_kaggle < 1e6 else None  # Only truncate reasonable times
    
    live_feats = compute_fixed(addr, live_data[addr], truncate_time=truncate)
    
    print(f"\n{addr} (truncate: {truncate/60 if truncate else 'N/A'}min):")
    
    mismatch_count = 0
    for feat in non_erc20_features:
        kaggle_val = kaggle_row[feat]
        live_val = live_feats[feat]
        
        if abs(kaggle_val) < 1e-10 and abs(live_val) < 1e-10:
            ratio = 1.0
        elif abs(kaggle_val) < 1e-10:
            ratio = 999.0
        elif abs(live_val) < 1e-10:
            ratio = 0.0
        else:
            ratio = live_val / kaggle_val
        
        match = 0.95 <= ratio <= 1.05
        if not match:
            mismatch_count += 1
            print(f"  ✗ {feat}: K={kaggle_val:.6f}, L={live_val:.6f}, ratio={ratio:.3f}")
        
        results.append({
            'address': addr[:10],
            'feature': feat,
            'kaggle': kaggle_val,
            'live': live_val,
            'ratio': ratio,
            'match': match
        })
    
    if mismatch_count == 0:
        print(f"  ✓ ALL 22 FEATURES MATCH")
    else:
        print(f"  Mismatches: {mismatch_count}/22")

# Summary table
df = pd.DataFrame(results)
print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
for addr in test_addresses:
    subset = df[df['address'] == addr[:10]]
    exact = (subset['ratio'] == 1.0).sum()
    close = ((subset['ratio'] >= 0.95) & (subset['ratio'] <= 1.05)).sum()
    print(f"{addr[:10]}: {exact}/22 exact, {close}/22 close (0.95-1.05)")

print(f"{'='*80}")
