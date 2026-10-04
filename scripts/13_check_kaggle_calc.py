import pandas as pd
import os

path = os.path.join(os.path.dirname(__file__), '..', 'data', 'splits', 'ethereum', 'test.csv')
df = pd.read_csv(path)

# Wallet 1: 2 sent txs
w1 = df[df['Address'] == '0x490d29b8669823e12eb5f72d53c27ebe7f952ab4'].iloc[0]
print(f"Wallet 1: 0x490d29b8...")
print(f"  Sent tnx: {w1['Sent tnx']}")
print(f"  Avg min between sent: {w1['Avg min between sent tnx']}")
print(f"  Received tnx: {w1['Received Tnx']}")
print(f"  Avg min between received: {w1['Avg min between received tnx']}")
print(f"  Time diff first-last: {w1['Time Diff between first and last (Mins)']}")
print(f"  If diff() method: {w1['Time Diff between first and last (Mins)']} / 1 = {w1['Time Diff between first and last (Mins)']/1}")
print(f"  But Kaggle Avg = {w1['Avg min between sent tnx']}")
print(f"  Ratio: {w1['Avg min between sent tnx']} / {w1['Time Diff between first and last (Mins)']} = {w1['Avg min between sent tnx'] / w1['Time Diff between first and last (Mins)']}")
print()

# Wallet 2: 2 sent, 3 received
w2 = df[df['Address'] == '0x85ef23bf9503300df9273725166503a1fc18c1b7'].iloc[0]
print(f"Wallet 2: 0x85ef23bf...")
print(f"  Sent tnx: {w2['Sent tnx']}")
print(f"  Avg min between sent: {w2['Avg min between sent tnx']}")
print(f"  Received tnx: {w2['Received Tnx']}")
print(f"  Avg min between received: {w2['Avg min between received tnx']}")
print(f"  Time diff first-last: {w2['Time Diff between first and last (Mins)']}")
print(f"  For 2 sent over {w2['Time Diff between first and last (Mins)']}min:")
print(f"    total_time/(n-1) = {w2['Time Diff between first and last (Mins)']}/(2-1) = {w2['Time Diff between first and last (Mins)']/1}")
print(f"    But Kaggle = {w2['Avg min between sent tnx']}")
print(f"    Ratio: {w2['Avg min between sent tnx']} / {w2['Time Diff between first and last (Mins)']} = {w2['Avg min between sent tnx'] / w2['Time Diff between first and last (Mins)']}")
