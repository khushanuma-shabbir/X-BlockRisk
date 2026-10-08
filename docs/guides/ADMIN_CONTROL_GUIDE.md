# Admin-Control Risk Detection Guide

## Overview

The Admin-Control Risk component evaluates smart contract owner powers and adjusts the risk score based on token establishment context.

## Thresholds (Constants)

```python
ESTABLISHED_LIQUIDITY_USD = 5_000_000  # $5M USD
ESTABLISHED_AGE_DAYS = 365  # 1 year
```

## Scoring System

### Admin Powers Evaluated (8 total)

| Power | Points | Description |
|-------|--------|-------------|
| Can mint tokens | 15 | Owner can create new tokens |
| Has blacklist | 15 | Owner can block addresses |
| Can pause trading | 12 | Owner can halt all trades |
| High fees | 10 | Excessive transaction fees |
| Trading limits | 8 | Max transaction restrictions |
| Trading switch | 12 | Owner controls trading on/off |
| Can withdraw liquidity | 18 | Owner can drain liquidity pool |
| Owner active | 10 | Owner actively changes balances |

**Maximum Raw Score**: 100 points (if all 8 powers present)

## Context Adjustment

### Established Token Criteria
A token is considered "established" when **BOTH** conditions are met:
- Liquidity ≥ $5,000,000 USD
- Age ≥ 365 days

### Adjustment Multiplier
- **Established token**: Raw score × **0.25**
- **New/small token**: Raw score × **1.0** (no adjustment)

### Reasoning
Admin powers (mint, pause, blacklist, etc.) are COMMON in established DeFi protocols like:
- Aave (can pause)
- Compound (has admin controls)
- Uniswap governance tokens (mint capability)
- USDC (blacklist for compliance)

These powers are **lower risk** when:
1. Token has survived 1+ year
2. Significant liquidity locked ($5M+)
3. Community has vetted the project

## Output Format

### New Token Example
```
🔐 Admin-Control Risk:
   Raw score: 60.0/100
   Adjusted score: 60.0/100
   ⚠ New/small token: $50,000 liquidity, 30 days old
   🔐 Owner can mint tokens
   🔐 Owner can blacklist addresses
   🔐 Owner can pause trading
   🚨 Owner can withdraw liquidity
```

### Established Token Example
```
🔐 Admin-Control Risk:
   Raw score: 60.0/100
   Adjusted score: 15.0/100
   ✅ Established token: $10,000,000 liquidity, 500 days old
   ℹ️ Admin powers are common and lower risk for established tokens
   🔐 Owner can mint tokens
   🔐 Owner can blacklist addresses
   🔐 Owner can pause trading
   🚨 Owner can withdraw liquidity
```

## Required Features

For admin-control detection to work, features dict must contain:

### Admin Power Features (binary 0/1)
- `can_mint`
- `has_blacklist`
- `can_pause`
- `fee_too_high`
- `has_trading_limits`
- `has_trading_cooldown`
- `owner_can_withdraw`
- `owner_change_balance`

### Context Features (numeric)
- `total_liquidity_usd` (float, USD value)
- `pair_created_days` (float, age in days)

## Integration Example

```python
from src.detection.hybrid_detector import HybridDetector

detector = HybridDetector()

# Token features (from contract analysis + DEX data)
features = {
    # Admin powers
    'can_mint': 1,
    'has_blacklist': 1,
    'can_pause': 1,
    'owner_can_withdraw': 1,
    
    # Context
    'total_liquidity_usd': 10_000_000,  # $10M
    'pair_created_days': 500,  # 500 days old
    
    # Transaction data
    'Sent tnx': 100,
    'Received Tnx': 50,
    # ... other features
}

# Get detection results
final_score, category, explanations = detector.detect(
    address='0x1234...',
    features=features,
    gnn_score=10.0
)

# Or get detailed summary
summary = detector.get_detection_summary(
    address='0x1234...',
    features=features,
    gnn_score=10.0
)

print(f"Raw admin score: {summary['admin_control_raw']}")
print(f"Adjusted admin score: {summary['admin_control_adjusted']}")
```

## Testing

```bash
# Run comprehensive tests
python src/detection/hybrid_detector.py

# Run focused admin-control tests
python test_admin_control.py
```

## Impact on Final Score

The adjusted admin-control score contributes to the ensemble with a **0.3 weight**:

```python
final_score = (
    gnn_weight * gnn_score +           # 40%
    rule_weight * rule_score +         # 35%
    blacklist_weight * blacklist_score # 25%
) + adjusted_admin_score * 0.3        # Additional risk factor
```

## Real-World Examples

### Established DeFi Protocol
- **Aave**: ~$6B liquidity, 4+ years old
  - Can pause: ✓ (emergency mechanism)
  - Admin controls: ✓ (governance)
  - **Risk**: LOW (established, battle-tested)

### New Token Red Flags
- **Liquidity**: $10,000 (very low)
- **Age**: 7 days (brand new)
- **Owner can withdraw liquidity**: ✓
- **Can mint unlimited tokens**: ✓
  - **Risk**: HIGH (potential rug pull)

## Customization

To adjust thresholds, edit constants at top of `src/detection/hybrid_detector.py`:

```python
# More conservative (stricter established criteria)
ESTABLISHED_LIQUIDITY_USD = 10_000_000  # $10M
ESTABLISHED_AGE_DAYS = 730  # 2 years

# More lenient (easier to qualify as established)
ESTABLISHED_LIQUIDITY_USD = 1_000_000  # $1M
ESTABLISHED_AGE_DAYS = 180  # 6 months
```

## Design Decisions

### Why 0.25× multiplier?
- Reduces admin-control impact by 75%
- Acknowledges that established projects need admin powers for:
  - Emergency pauses (security)
  - Compliance (blacklist for regulations)
  - Governance (upgrades, parameters)
- Still penalizes owner powers, just less severely

### Why both liquidity AND age?
- **Liquidity alone**: Large initial liquidity can be fake
- **Age alone**: Old inactive projects aren't safer
- **Both together**: Strong signal of legitimacy

### Why these specific thresholds?
- **$5M USD**: Significant capital at risk, requires trust
- **365 days**: Full year of market cycles, community vetting

## Future Enhancements

Potential improvements:
1. **Graduated multipliers**: 0.5× at 6 months, 0.25× at 1 year
2. **Audit bonus**: Further reduction if audited by reputable firms
3. **Governance check**: Lower risk if governed by DAO
4. **Track record**: Analyze owner's historical behavior
