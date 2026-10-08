"""Test the context aware analyzer directly"""

from src.analysis.context_aware_analyzer import ContextAwareAnalyzer

analyzer = ContextAwareAnalyzer()

# Test USDT address
address = "0xdAC17F958D2ee523a2206206994597C13d831ec7"
final_score = 26.04
features = {
    'total_liquidity_usd': 184_000_000_000,  # $184B
    'Time Diff between first and last (Mins)': 3_000_000,  # ~2000 days
    'Sent tnx': 50_000_000,
    'Received Tnx': 50_000_000,
    'can_mint': 1,
    'has_blacklist': 1,
    'can_pause': 1,
}

result = analyzer.analyze_with_context(
    address=address,
    final_score=final_score,
    features=features,
    is_contract=True,
    explanations=[]
)

print("="*80)
print("CONTEXT ANALYSIS TEST - USDT")
print("="*80)
print(f"\nRisk Level: {result['risk_level']}")
print(f"\nSummary:\n{result['summary']}")
print(f"\nToken Info: {result['token_info']}")
print(f"\nContext Explanation:\n{result['context_explanation']}")
print(f"\nActivity Explanation:\n{result['activity_explanation']}")
print(f"\nRecommendations:")
for rec in result['recommendations']:
    print(f"  {rec}")
print(f"\nVerdict:\n{result['verdict']}")
print("\n" + "="*80)
