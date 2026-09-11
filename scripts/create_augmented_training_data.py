"""
SOLUTION: Augment training data with high-activity versions of fraud patterns
This will make the model work on live Ethereum addresses

Strategy:
1. Take existing fraud patterns from training data
2. Scale them up (multiply transaction counts, ETH amounts)
3. Create "high-activity fraud" versions
4. Add to training data
5. Retrain model

Result: Model will work on both low-activity AND high-activity addresses
"""

import pandas as pd
import numpy as np

# Load original training data
df = pd.read_csv('data/processed/ethereum_clean.csv')

print("="*70)
print("CREATING AUGMENTED TRAINING DATA")
print("="*70)

# Separate fraud and legitimate
fraud_df = df[df['FLAG'] == 1].copy()
legit_df = df[df['FLAG'] == 0].copy()

print(f"\nOriginal data:")
print(f"  Fraud: {len(fraud_df)}")
print(f"  Legitimate: {len(legit_df)}")

# Define scaling factors (multiply by these to create high-activity versions)
scaling_factors = [5, 10, 20, 50, 100]

augmented_fraud = []

for scale in scaling_factors:
    scaled = fraud_df.copy()
    
    # Scale transaction counts
    scaled['Sent tnx'] = (scaled['Sent tnx'] * scale).clip(upper=10000)
    scaled['Received Tnx'] = (scaled['Received Tnx'] * scale).clip(upper=10000)
    
    # Scale ETH amounts
    scaled['total Ether sent'] = (scaled['total Ether sent'] * scale).clip(upper=1000000)
    scaled['total ether received'] = (scaled['total ether received'] * scale).clip(upper=1000000)
    
    # Scale unique addresses (but not as much - fraudsters still contact similar number)
    scaled['Unique Sent To Addresses'] = (scaled['Unique Sent To Addresses'] * np.sqrt(scale)).clip(upper=1000)
    scaled['Unique Received From Addresses'] = (scaled['Unique Received From Addresses'] * np.sqrt(scale)).clip(upper=1000)
    
    # Update derived features
    if 'Sent tnx' in scaled.columns and scaled['Sent tnx'].sum() > 0:
        scaled['avg val sent'] = scaled['total Ether sent'] / scaled['Sent tnx'].replace(0, 1)
    
    if 'Received Tnx' in scaled.columns and scaled['Received Tnx'].sum() > 0:
        scaled['avg val received'] = scaled['total ether received'] / scaled['Received Tnx'].replace(0, 1)
    
    # Recalculate balance
    scaled['total ether balance'] = scaled['total ether received'] - scaled['total Ether sent']
    
    # Keep other features proportional
    # Time-based features stay similar (fraudsters still act fast)
    # But scale the total time span
    scaled['Time Diff between first and last (Mins)'] = (scaled['Time Diff between first and last (Mins)'] * np.sqrt(scale)).clip(upper=1000000)
    
    augmented_fraud.append(scaled)
    print(f"  Created {len(scaled)} fraud samples at scale x{scale}")

# Combine original + augmented
all_fraud = pd.concat([fraud_df] + augmented_fraud, ignore_index=True)

print(f"\nAugmented fraud data: {len(all_fraud)} samples")

# Also create high-activity legitimate samples
augmented_legit = []

for scale in [5, 10, 20]:  # Fewer scales for legitimate (already higher activity)
    scaled = legit_df.copy()
    
    # Scale transaction counts
    scaled['Sent tnx'] = (scaled['Sent tnx'] * scale).clip(upper=50000)
    scaled['Received Tnx'] = (scaled['Received Tnx'] * scale).clip(upper=50000)
    
    # Scale ETH amounts
    scaled['total Ether sent'] = (scaled['total Ether sent'] * scale).clip(upper=10000000)
    scaled['total ether received'] = (scaled['total ether received'] * scale).clip(upper=10000000)
    
    # Scale unique addresses
    scaled['Unique Sent To Addresses'] = (scaled['Unique Sent To Addresses'] * np.sqrt(scale)).clip(upper=5000)
    scaled['Unique Received From Addresses'] = (scaled['Unique Received From Addresses'] * np.sqrt(scale)).clip(upper=5000)
    
    # Update derived features
    if 'Sent tnx' in scaled.columns and scaled['Sent tnx'].sum() > 0:
        scaled['avg val sent'] = scaled['total Ether sent'] / scaled['Sent tnx'].replace(0, 1)
    
    if 'Received Tnx' in scaled.columns and scaled['Received Tnx'].sum() > 0:
        scaled['avg val received'] = scaled['total ether received'] / scaled['Received Tnx'].replace(0, 1)
    
    scaled['total ether balance'] = scaled['total ether received'] - scaled['total Ether sent']
    scaled['Time Diff between first and last (Mins)'] = (scaled['Time Diff between first and last (Mins)'] * np.sqrt(scale)).clip(upper=10000000)
    
    augmented_legit.append(scaled)
    print(f"  Created {len(scaled)} legitimate samples at scale x{scale}")

# Combine all data
all_legit = pd.concat([legit_df] + augmented_legit, ignore_index=True)

print(f"\nAugmented legitimate data: {len(all_legit)} samples")

# Combine fraud + legitimate
augmented_df = pd.concat([all_fraud, all_legit], ignore_index=True)

# Shuffle
augmented_df = augmented_df.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\n{'='*70}")
print(f"FINAL AUGMENTED DATASET")
print(f"{'='*70}")
print(f"Total samples: {len(augmented_df)}")
print(f"  Fraud: {len(augmented_df[augmented_df['FLAG'] == 1])}")
print(f"  Legitimate: {len(augmented_df[augmented_df['FLAG'] == 0])}")

# Show statistics
print(f"\n{'='*70}")
print(f"STATISTICS COMPARISON")
print(f"{'='*70}")

print(f"\nFRAUD - Original vs Augmented:")
print(f"  Original avg sent txs: {fraud_df['Sent tnx'].mean():.1f}")
print(f"  Augmented avg sent txs: {all_fraud['Sent tnx'].mean():.1f}")
print(f"  Original avg total ETH: {fraud_df['total Ether sent'].mean():.2f}")
print(f"  Augmented avg total ETH: {all_fraud['total Ether sent'].mean():.2f}")

print(f"\nLEGITIMATE - Original vs Augmented:")
print(f"  Original avg sent txs: {legit_df['Sent tnx'].mean():.1f}")
print(f"  Augmented avg sent txs: {all_legit['Sent tnx'].mean():.1f}")
print(f"  Original avg total ETH: {legit_df['total Ether sent'].mean():.2f}")
print(f"  Augmented avg total ETH: {all_legit['total Ether sent'].mean():.2f}")

# Save augmented dataset
output_path = 'data/processed/ethereum_augmented.csv'
augmented_df.to_csv(output_path, index=False)

print(f"\n{'='*70}")
print(f"SAVED AUGMENTED DATASET")
print(f"{'='*70}")
print(f"File: {output_path}")
print(f"Size: {len(augmented_df)} samples")

print(f"\n{'='*70}")
print(f"NEXT STEP: RETRAIN MODEL")
print(f"{'='*70}")
print("""
Run this command to retrain on augmented data:

python src/models/train_gnn.py \\
    --data data/processed/ethereum_augmented.csv \\
    --output models/ethereum/model_augmented.pt

This will create a new model that works on BOTH:
- Low-activity addresses (original training)
- High-activity addresses (augmented data)

Then update app.py to use model_augmented.pt instead of model_tuned.pt
""")
