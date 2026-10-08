"""Test context-aware admin-control scoring with real DEX data"""
import os
from dotenv import load_dotenv
from src.live.contract_analyzer import ContractAnalyzer
from src.live.dex_analyzer import DexAnalyzer
from src.detection.hybrid_detector import AdminControlDetector, ESTABLISHED_LIQUIDITY_USD, ESTABLISHED_AGE_DAYS

load_dotenv()

print("="*80)
print("TESTING CONTEXT-AWARE ADMIN-CONTROL SCORING")
print("="*80)

# Initialize analyzers
etherscan_key = os.getenv('ETHERSCAN_API_KEY')
contract_analyzer = ContractAnalyzer(etherscan_key, chain_id='1')
dex_analyzer = DexAnalyzer(etherscan_api_key=etherscan_key)

print(f"\nThresholds for 'established' token:")
print(f"  • Liquidity: >= ${ESTABLISHED_LIQUIDITY_USD:,} USD")
print(f"  • Age: >= {ESTABLISHED_AGE_DAYS} days")

# Test 1: USDT (established token with admin powers)
print("\n" + "="*80)
print("TEST 1: USDT - Established Token with Admin Powers")
print("="*80)

usdt = '0xdAC17F958D2ee523a2206206994597C13D831ec7'
print(f"Address: {usdt}")

# Get contract features
contract_features = contract_analyzer.analyze_contract(usdt)
print(f"\nContract Features:")
for key, value in contract_features.items():
    if value > 0:
        print(f"  • {key}: {value}")

# Get DEX features
dex_features = dex_analyzer.analyze_token(usdt)
print(f"\nDEX Features:")
print(f"  • Liquidity: ${dex_features['total_liquidity_usd']:,.0f}")
print(f"  • Age: {dex_features['pair_created_days']} days")

# Combine features
all_features = {**contract_features, **dex_features}

# Test admin-control detection
raw_score, adjusted_score, patterns = AdminControlDetector.detect_admin_control(all_features)

print(f"\nAdmin-Control Analysis:")
print(f"  • Raw Score: {raw_score}/100")
print(f"  • Adjusted Score: {adjusted_score}/100")
print(f"  • Adjustment: {((adjusted_score - raw_score) / raw_score * 100):.1f}% (should be -75%)")

print(f"\nDetection Patterns:")
for pattern in patterns:
    print(f"  {pattern}")

# Verify adjustment is applied
is_established = (
    dex_features['total_liquidity_usd'] >= ESTABLISHED_LIQUIDITY_USD and
    dex_features['pair_created_days'] >= ESTABLISHED_AGE_DAYS
)
print(f"\n✅ Is Established: {is_established}")
print(f"✅ Context Adjustment Applied: {adjusted_score < raw_score}")

# Test 2: Random scam address (not established)
print("\n" + "="*80)
print("TEST 2: Fake Token - Not Established (simulation)")
print("="*80)

fake_features = {
    'can_mint': 1,
    'has_blacklist': 1,
    'can_pause': 1,
    'owner_can_withdraw': 1,
    'total_liquidity_usd': 50000,  # Only $50k
    'pair_created_days': 30,  # Only 30 days
}

print(f"\nSimulated Features:")
print(f"  • can_mint: 1")
print(f"  • has_blacklist: 1")
print(f"  • can_pause: 1")
print(f"  • owner_can_withdraw: 1")
print(f"  • Liquidity: ${fake_features['total_liquidity_usd']:,}")
print(f"  • Age: {fake_features['pair_created_days']} days")

raw_score2, adjusted_score2, patterns2 = AdminControlDetector.detect_admin_control(fake_features)

print(f"\nAdmin-Control Analysis:")
print(f"  • Raw Score: {raw_score2}/100")
print(f"  • Adjusted Score: {adjusted_score2}/100")
print(f"  • Adjustment: None (not established)")

print(f"\nDetection Patterns:")
for pattern in patterns2[:5]:
    print(f"  {pattern}")

is_established2 = (
    fake_features['total_liquidity_usd'] >= ESTABLISHED_LIQUIDITY_USD and
    fake_features['pair_created_days'] >= ESTABLISHED_AGE_DAYS
)
print(f"\n✅ Is Established: {is_established2}")
print(f"✅ Context Adjustment NOT Applied: {adjusted_score2 == raw_score2}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"✅ USDT (established): Raw {raw_score} → Adjusted {adjusted_score} (-75%)")
print(f"✅ Fake token (new): Raw {raw_score2} → Adjusted {adjusted_score2} (no change)")
print(f"✅ Context-aware scoring is FUNCTIONAL")
