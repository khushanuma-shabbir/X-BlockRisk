"""
Full parity check on 4 wallets: all 22 non-ERC20 features
"""

import pandas as pd
import numpy as np
import requests
import os
from dotenv import load_dotenv

load_dotenv()
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

# 4 test wallets (dormant, <10k tx)
test_addresses = [
    '0x490d29b8669823e12eb5f72d53c27ebe7f952ab4',  # Fraud, 10 tx
    '0xa68b5746deaf18481a4ba57b61b69872381c9535',  # Legit, 2 tx (shows 1 extra live)
    '0x85ef23bf9503300df9273725166503a1fc18c1b7',  # Legit, 5 tx
    '0x1b133fde5bff441c6afce6aaddd9fdcdf980735e',  # Legit, 12 tx
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
print("FULL PARITY: 4 WALLETS, 22 NON-ERC20 FEATURES")
print("="*80)

def fetch_v2(address):
    """Fetch using V2 API"""
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

def compute_features_live(address, txs):
    """Compute features matching Kaggle definitions"""
    if not txs:
        return {feat: 0.0 for feat in non_erc20_features}
    
    # Convert to DataFrame
    df = pd.DataFrame(txs)
    df['value'] = pd.to_numeric(df['value'], errors='coerce') / 1e18  # Wei to ETH
    df['timeStamp'] = pd.to_numeric(df['timeStamp'], errors='coerce')
    df['from'] = df['from'].str.lower()
    df['to'] = df['to'].str.lower()
    
    addr_lower = address.lower()
    
    # Separate sent/received
    sent = df[df['from'] == addr_lower]
    recv = df[(df['to'] == addr_lower) & (df['from'] != addr_lower)]
    
    features = {}
    
    # Time features
    if len(sent) > 1:
        sent_diffs = sent['timeStamp'].diff().dropna() / 60
        features['Avg min between sent tnx'] = sent_diffs.mean()
    else:
        features['Avg min between sent tnx'] = 0.0
    
    if len(recv) > 1:
        recv_diffs = recv['timeStamp'].diff().dropna() / 60
        features['Avg min between received tnx'] = recv_diffs.mean()
    else:
        features['Avg min between received tnx'] = 0.0
    
    if len(df) > 0:
        features['Time Diff between first and last (Mins)'] = (df['timeStamp'].max() - df['timeStamp'].min()) / 60
    else:
        features['Time Diff between first and last (Mins)'] = 0.0
    
    # Counts
    features['Sent tnx'] = len(sent)
    features['Received Tnx'] = len(recv)
    features['Number of Created Contracts'] = len(df[df['contractAddress'].notna()])
    features['Unique Received From Addresses'] = recv['from'].nunique()
    features['Unique Sent To Addresses'] = sent['to'].nunique()
    
    # Received values
    features['min value received'] = recv['value'].min() if len(recv) > 0 else 0.0
    features['max value received'] = recv['value'].max() if len(recv) > 0 else 0.0
    features['avg val received'] = recv['value'].mean() if len(recv) > 0 else 0.0
    
    # Sent values
    features['min val sent'] = sent['value'].min() if len(sent) > 0 else 0.0
    features['max val sent'] = sent['value'].max() if len(sent) > 0 else 0.0
    features['avg val sent'] = sent['value'].mean() if len(sent) > 0 else 0.0
    
    # Contract values (transactions that created a contract)
    contract_txs = sent[sent['contractAddress'].notna()]
    features['min value sent to contract'] = contract_txs['value'].min() if len(contract_txs) > 0 else 0.0
    features['max val sent to contract'] = contract_txs['value'].max() if len(contract_txs) > 0 else 0.0
    features['avg value sent to contract'] = contract_txs['value'].mean() if len(contract_txs) > 0 else 0.0
    
    # Totals
    features['total transactions (including tnx to create contract'] = len(df)
    features['total Ether sent'] = sent['value'].sum()
    features['total ether received'] = recv['value'].sum()
    features['total ether sent contracts'] = contract_txs['value'].sum()
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

print("\n[2/2] Computing features and comparing...")

for addr in test_addresses:
    kaggle_row = test_df[test_df['Address'] == addr].iloc[0]
    live_feats = compute_features_live(addr, live_data[addr])
    
    print(f"\n{'='*80}")
    print(f"WALLET: {addr}")
    print(f"FLAG: {kaggle_row['FLAG']} (1=fraud, 0=legit)")
    print(f"{'='*80}")
    print(f"{'Feature':<45} {'Kaggle':<15} {'Live':<15} {'Ratio':<10}")
    print("-"*80)
    
    mismatches = []
    
    for feat in non_erc20_features:
        kaggle_val = kaggle_row[feat]
        live_val = live_feats[feat]
        
        if kaggle_val == 0 and live_val == 0:
            ratio = 1.0
        elif abs(kaggle_val) < 1e-10:
            ratio = 999.0 if abs(live_val) > 1e-10 else 1.0
        elif abs(live_val) < 1e-10:
            ratio = 0.0
        else:
            ratio = live_val / kaggle_val
        
        match_symbol = "✓" if 0.95 <= ratio <= 1.05 else "✗"
        print(f"{feat:<45} {kaggle_val:<15.6f} {live_val:<15.6f} {ratio:<10.3f} {match_symbol}")
        
        if not (0.95 <= ratio <= 1.05) and abs(kaggle_val) > 0.001:
            mismatches.append((feat, kaggle_val, live_val, ratio))
    
    if mismatches:
        print(f"\nMISMATCHES ({len(mismatches)}):")
        for feat, kval, lval, ratio in mismatches:
            print(f"  {feat}: Kaggle={kval:.6f}, Live={lval:.6f}, Ratio={ratio:.3f}")

# Special analysis for wallet with extra transaction
print(f"\n{'='*80}")
print("TIMESTAMP ANALYSIS FOR 0xa68b5746...")
print(f"{'='*80}")
addr_special = '0xa68b5746deaf18481a4ba57b61b69872381c9535'
txs_special = live_data[addr_special]
if txs_special:
    print(f"Found {len(txs_special)} transactions:")
    for i, tx in enumerate(txs_special, 1):
        ts = int(tx['timeStamp'])
        from datetime import datetime
        dt = datetime.fromtimestamp(ts)
        print(f"  {i}. {dt.strftime('%Y-%m-%d %H:%M:%S')} | From: {tx['from'][:10]}... | To: {tx['to'][:10]}... | Value: {float(tx['value'])/1e18:.6f} ETH")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("Definition/unit problems vs new activity:")
print("  - Exact matches (ratio ~1.0): Definitions align")
print("  - Mismatches with consistent pattern: Definition/unit issue")
print("  - Extra transactions: New activity after dataset snapshot (check timestamps)")
print("="*80)
