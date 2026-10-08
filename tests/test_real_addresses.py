"""
Test on REAL Ethereum addresses from Etherscan
Tests live addresses to show system works in production
"""

import os
from dotenv import load_dotenv
from src.live.fetch_ethereum import fetch_and_analyze_address

load_dotenv()

print("="*80)
print("REAL ADDRESS TESTING")
print("="*80)
print()

# Real addresses to test
test_cases = [
    {
        'name': 'Known Phishing',
        'address': '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',
        'expected': 'High Risk',
        'description': 'Fake_Phishing (Etherscan labeled)'
    },
    {
        'name': 'USDT Contract',
        'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'expected': 'Low Risk',
        'description': 'Legitimate stablecoin with high liquidity'
    },
    {
        'name': 'Vitalik.eth',
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'expected': 'Low Risk',
        'description': 'Ethereum founder - legitimate address'
    },
    {
        'name': 'Uniswap Router',
        'address': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        'expected': 'Low Risk',
        'description': 'Popular DEX router contract'
    },
]

results = []

for i, test in enumerate(test_cases, 1):
    print(f"[{i}/{len(test_cases)}] Testing: {test['name']}")
    print("-"*80)
    print(f"Address: {test['address']}")
    print(f"Description: {test['description']}")
    print(f"Expected: {test['expected']}")
    print()
    
    try:
        # Analyze address
        result = fetch_and_analyze_address(
            test['address'],
            'ethereum',
            use_cache=True
        )
        
        final_score = result['analysis']['final_risk_score']
        category = result['analysis']['risk_category']
        
        # Check if matches expected
        match = "✓" if test['expected'] == category else "✗"
        
        print(f"Result: {final_score:.1f}/100 ({category}) {match}")
        
        results.append({
            'name': test['name'],
            'expected': test['expected'],
            'actual': category,
            'score': final_score,
            'match': test['expected'] == category
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        results.append({
            'name': test['name'],
            'expected': test['expected'],
            'actual': 'ERROR',
            'score': 0,
            'match': False
        })
    
    print()
    print("="*80)
    print()

# Summary
print("RESULTS SUMMARY")
print("="*80)
print()

passed = sum(1 for r in results if r['match'])
total = len(results)

print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
print()

for r in results:
    status = "✓ PASS" if r['match'] else "✗ FAIL"
    print(f"{status} | {r['name']:20s} | Expected: {r['expected']:12s} | Got: {r['actual']:12s} ({r['score']:.1f}/100)")

print()
print("="*80)
