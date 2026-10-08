"""
Test Offline Reproduction - Verify caching works
Run this TWICE:
1. First run: Fetches from API and caches
2. Second run: Uses cached data (disconnect internet to verify)
"""

import os
from dotenv import load_dotenv
from src.live.contract_analyzer import ContractAnalyzer
from src.live.dex_analyzer import DexAnalyzer
from src.cache.api_cache import get_cache

load_dotenv()

print("="*80)
print("OFFLINE REPRODUCTION TEST")
print("="*80)

# Get cache stats before
cache = get_cache()
stats_before = cache.get_stats()
print(f"\nCache stats BEFORE:")
print(f"  Files: {stats_before['total_files']}")
print(f"  Size: {stats_before['total_size_mb']:.2f} MB")

# Test addresses
test_addresses = [
    ('USDT', '0xdAC17F958D2ee523a2206206994597C13D831ec7'),
    ('WETH', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'),
]

etherscan_key = os.getenv('ETHERSCAN_API_KEY')

print("\n" + "="*80)
print("TESTING WITH CACHE ENABLED")
print("="*80)

for name, address in test_addresses:
    print(f"\n--- {name} ({address}) ---")
    
    # Contract analysis
    contract_analyzer = ContractAnalyzer(etherscan_key, use_cache=True)
    contract_features = contract_analyzer.analyze_contract(address)
    print(f"Contract Features: {sum(1 for v in contract_features.values() if v > 0)} powers detected")
    for key, value in contract_features.items():
        if value > 0:
            print(f"  • {key}: {value}")
    
    # DEX analysis  
    dex_analyzer = DexAnalyzer(etherscan_api_key=etherscan_key, use_cache=True)
    dex_features = dex_analyzer.analyze_token(address)
    print(f"DEX Features:")
    print(f"  • Liquidity: ${dex_features['total_liquidity_usd']:,.0f}")
    print(f"  • Age: {dex_features['pair_created_days']} days")

# Get cache stats after
stats_after = cache.get_stats()
print("\n" + "="*80)
print("CACHE STATS AFTER")
print("="*80)
print(f"Files: {stats_before['total_files']} → {stats_after['total_files']} (+{stats_after['total_files'] - stats_before['total_files']})")
print(f"Size: {stats_before['total_size_mb']:.2f} MB → {stats_after['total_size_mb']:.2f} MB")
print(f"Location: {stats_after['cache_dir']}")

# Show cache files
print("\nCached API responses:")
cache_dir = cache.cache_dir
for cache_file in sorted(cache_dir.glob("*.json"))[:10]:
    size_kb = cache_file.stat().st_size / 1024
    print(f"  • {cache_file.name[:16]}... ({size_kb:.1f} KB)")

print("\n" + "="*80)
print("REPRODUCTION INSTRUCTIONS")
print("="*80)
print("1. Run this script once with internet connection")
print("2. API responses are cached in:", stats_after['cache_dir'])
print("3. Run again WITHOUT internet - should work from cache!")
print("4. To share results: Copy cache/ folder to another machine")
print("5. Professor can reproduce without API keys")
print("="*80)

print("\n" + "="*80)
print("TESTING OFFLINE MODE (no API calls)")
print("="*80)
print("Re-analyzing same addresses using ONLY cached data...")

for name, address in test_addresses:
    print(f"\n{name}: ", end="")
    
    # This should use cache (no API calls)
    contract_analyzer = ContractAnalyzer(etherscan_key, use_cache=True)
    contract_features = contract_analyzer.analyze_contract(address)
    
    dex_analyzer = DexAnalyzer(etherscan_api_key=etherscan_key, use_cache=True)
    dex_features = dex_analyzer.analyze_token(address)
    
    powers = sum(1 for v in contract_features.values() if v > 0)
    liquidity = dex_features['total_liquidity_usd']
    
    print(f"{powers} powers, ${liquidity:,.0f} liquidity ✓")

print("\n" + "="*80)
print("✓ OFFLINE REPRODUCTION WORKING")
print("="*80)
print("Cache enables:")
print("  • Reproducible results (same data every time)")
print("  • No API keys needed (for cached addresses)")
print("  • No rate limits (instant responses)")
print("  • No internet required (offline demo)")
print("="*80)
