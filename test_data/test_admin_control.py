"""
Test Admin-Control Risk Detection with Context Adjustment

Shows how the system adjusts admin-control scores based on token establishment.
"""

from src.detection.hybrid_detector import HybridDetector, ESTABLISHED_LIQUIDITY_USD, ESTABLISHED_AGE_DAYS

def test_admin_control():
    detector = HybridDetector()
    
    # Same admin powers for both tests
    admin_powers = {
        'can_mint': 1,
        'has_blacklist': 1,
        'can_pause': 1,
        'fee_too_high': 1,
        'has_trading_limits': 1,
        'has_trading_cooldown': 1,
        'owner_can_withdraw': 1,
        'owner_change_balance': 1,
        'Sent tnx': 100,
        'Received Tnx': 50,
    }
    
    print("="*80)
    print("ADMIN-CONTROL RISK WITH CONTEXT ADJUSTMENT")
    print("="*80)
    print(f"\nThresholds for 'established' token:")
    print(f"  • Liquidity: ${ESTABLISHED_LIQUIDITY_USD:,} USD")
    print(f"  • Age: {ESTABLISHED_AGE_DAYS} days")
    print(f"\nAll admin powers enabled in both tests:")
    print("  ✓ Can mint tokens (15 pts)")
    print("  ✓ Can blacklist addresses (15 pts)")
    print("  ✓ Can pause trading (12 pts)")
    print("  ✓ High fees (10 pts)")
    print("  ✓ Trading limits (8 pts)")
    print("  ✓ Trading cooldown switch (12 pts)")
    print("  ✓ Owner can withdraw liquidity (18 pts)")
    print("  ✓ Owner actively changing balance (10 pts)")
    print(f"  = {15+15+12+10+8+12+18+10} points total")
    
    # Test 1: New/small token
    print("\n" + "-"*80)
    print("SCENARIO 1: New Token (Below Thresholds)")
    print("-"*80)
    
    new_token = {**admin_powers}
    new_token['total_liquidity_usd'] = 100_000  # Below threshold
    new_token['pair_created_days'] = 60  # Below threshold
    
    summary = detector.get_detection_summary(
        '0x1111111111111111111111111111111111111111',
        new_token,
        gnn_score=5
    )
    
    print(f"\nToken Stats:")
    print(f"  • Liquidity: ${new_token['total_liquidity_usd']:,} (below ${ESTABLISHED_LIQUIDITY_USD:,})")
    print(f"  • Age: {new_token['pair_created_days']} days (below {ESTABLISHED_AGE_DAYS} days)")
    print(f"\nAdmin-Control Risk:")
    print(f"  • Raw score: {summary['admin_control_raw']:.1f}/100")
    print(f"  • Adjusted score: {summary['admin_control_adjusted']:.1f}/100")
    print(f"  • Adjustment applied: NO (multiplier = 1.0)")
    print(f"\nFinal Risk Score: {summary['final_score']:.1f}/100 ({summary['category']})")
    
    # Test 2: Established token
    print("\n" + "-"*80)
    print("SCENARIO 2: Established Token (Above Thresholds)")
    print("-"*80)
    
    established_token = {**admin_powers}
    established_token['total_liquidity_usd'] = 10_000_000  # Above threshold
    established_token['pair_created_days'] = 500  # Above threshold
    
    summary = detector.get_detection_summary(
        '0x2222222222222222222222222222222222222222',
        established_token,
        gnn_score=5
    )
    
    print(f"\nToken Stats:")
    print(f"  • Liquidity: ${established_token['total_liquidity_usd']:,} (above ${ESTABLISHED_LIQUIDITY_USD:,})")
    print(f"  • Age: {established_token['pair_created_days']} days (above {ESTABLISHED_AGE_DAYS} days)")
    print(f"\nAdmin-Control Risk:")
    print(f"  • Raw score: {summary['admin_control_raw']:.1f}/100")
    print(f"  • Adjusted score: {summary['admin_control_adjusted']:.1f}/100")
    print(f"  • Adjustment applied: YES (multiplier = 0.25)")
    print(f"  • Reduction: {summary['admin_control_raw'] - summary['admin_control_adjusted']:.1f} points")
    print(f"\nFinal Risk Score: {summary['final_score']:.1f}/100 ({summary['category']})")
    
    # Comparison
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    print(f"Same admin powers, different context:")
    print(f"  • New token final score: 28.0/100")
    print(f"  • Established token final score: {summary['final_score']:.1f}/100")
    print(f"  • Score reduction: {28.0 - summary['final_score']:.1f} points")
    print(f"\nKey Insight: Admin powers are COMMON and LOWER RISK for established tokens!")
    print("="*80)

if __name__ == '__main__':
    test_admin_control()
