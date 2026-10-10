"""
Precision-Focused Fraud Detector
Prevents false positives on legitimate addresses
"""

from typing import Tuple, List, Dict

class PrecisionDetector:
    """
    High-precision fraud detection with whitelist and multi-signal confirmation
    Prevents false positives on major tokens and known addresses
    """
    
    # Verified safe addresses (0% false positive rate)
    VERIFIED_SAFE = {
        # Major Stablecoins
        '0xdac17f958d2ee523a2206206994597c13d831ec7': 'USDT - Tether USD',
        '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDC - USD Coin',
        '0x6b175474e89094c44da98b954eedeac495271d0f': 'DAI - MakerDAO',
        '0x4fabb145d64652a948d72533023f6e7a623c7c53': 'BUSD - Binance USD',
        
        # Major Tokens
        '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 'WETH - Wrapped Ether',
        '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'WBTC - Wrapped Bitcoin',
        '0x514910771af9ca656af840dff83e8264ecf986ca': 'LINK - Chainlink',
        '0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0': 'MATIC - Polygon',
        '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984': 'UNI - Uniswap',
        
        # Major DeFi Protocols
        '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2 Router',
        '0xe592427a0aece92de3edee1f18e0157c05861564': 'Uniswap V3 Router',
        '0x881d40237659c251811cec9c364ef91dc08d300c': 'Metamask Swap Router',
        '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': 'Aave Lending Pool',
        '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b': 'Compound Comptroller',
        
        # Exchange Wallets
        '0x28c6c06298d514db089934071355e5743bf21d60': 'Binance 14',
        '0x21a31ee1afc51d94c2efccaa2092ad1028285549': 'Binance 15',
        '0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be': 'Binance 16',
        '0xdfd5293d8e347dfe59e90efd55b2956a1343963d': 'Binance Cold Wallet',
        '0x56eddb7aa87536c09ccc2793473599fd21a8b17f': 'Binance 17',
        '0x9696f59e4d72e237be84ffd425dcad154bf96976': 'Binance 18',
        '0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67': 'Binance 19',
        
        # Famous Addresses
        '0xd8da6bf26964af9d7eed9e03e53415d37aa96045': 'vitalik.eth - Vitalik Buterin',
        '0xab5801a7d398351b8be11c439e05c5b3259aec9b': 'Vitalik Buterin',
        
        # ETH2
        '0x00000000219ab540356cbb839cbe05303d7705fa': 'ETH2 Deposit Contract',
    }
    
    def __init__(self, base_detector):
        self.base_detector = base_detector
    
    def detect(
        self,
        address: str,
        features: Dict,
        gnn_score: float
    ) -> Tuple[float, str, List[str]]:
        """
        High-precision detection with whitelist and multi-signal logic
        
        Returns:
            (final_score, category, explanations)
        """
        address_lower = address.lower()
        
        # STEP 1: Check whitelist (100% precision)
        if address_lower in self.VERIFIED_SAFE:
            token_name = self.VERIFIED_SAFE[address_lower]
            
            # Return IMMEDIATELY - don't run base detector at all
            explanations = [
                f"✅ VERIFIED SAFE: {token_name}",
                "📋 This address is on our verified safe list",
                "🛡️ Used by millions daily on major platforms",
                "ℹ️ No fraud risk detected"
            ]
            
            # Also need to build a proper summary for get_detection_summary
            # Return score of 5 (very safe)
            return (5.0, "Very Low Risk", explanations)
        
        # STEP 2: Check if established token
        liquidity = features.get('total_liquidity_usd', 0)
        age_mins = features.get('Time Diff between first and last (Mins)', 0)
        age_days = age_mins / 1440 if age_mins > 0 else 0
        
        is_mega_established = liquidity >= 1_000_000_000 and age_days >= 365
        is_established = liquidity >= 100_000_000 and age_days >= 180
        
        # STEP 3: Run base detection
        base_score, base_category, base_explanations = self.base_detector.detect(
            address, features, gnn_score
        )
        
        # STEP 4: Apply precision adjustments
        
        # For mega established tokens ($1B+, 1+ year)
        if is_mega_established:
            # These are almost certainly legitimate
            # Reduce score significantly
            adjusted_score = base_score * 0.3  # 70% reduction
            
            if adjusted_score < 30:
                category = "Very Low Risk"
                explanations = base_explanations + [
                    "",
                    "🔷 ESTABLISHED TOKEN ADJUSTMENT:",
                    f"   💰 Liquidity: ${liquidity:,.0f}",
                    f"   📅 Age: {age_days:.0f} days ({age_days/365:.1f} years)",
                    "   ✅ Size and longevity indicate legitimacy",
                    f"   📉 Risk score reduced: {base_score:.1f} → {adjusted_score:.1f}",
                ]
            else:
                category = "Low Risk"
                explanations = base_explanations + [
                    "",
                    "⚠️ UNUSUAL: Established token with some risk indicators",
                    f"   Original score: {base_score:.1f}",
                    f"   Adjusted for size: {adjusted_score:.1f}",
                ]
            
            return (adjusted_score, category, explanations)
        
        # For established tokens ($100M+, 6+ months)
        elif is_established:
            # Moderate reduction
            adjusted_score = base_score * 0.6  # 40% reduction
            
            if adjusted_score < 35:
                category = "Low Risk"
                explanations = base_explanations + [
                    "",
                    "🔷 ESTABLISHED TOKEN ADJUSTMENT:",
                    f"   💰 Liquidity: ${liquidity:,.0f}",
                    f"   📅 Age: {age_days:.0f} days",
                    f"   📉 Risk reduced: {base_score:.1f} → {adjusted_score:.1f}",
                ]
            else:
                category = "Medium Risk"
                explanations = base_explanations
            
            return (adjusted_score, category, explanations)
        
        # STEP 5: Multi-signal confirmation for high risk
        if base_score >= 70:
            # Require multiple signals for HIGH RISK classification
            signals = self._count_risk_signals(features, base_explanations)
            
            if signals >= 3:
                # 3+ signals → Confident it's fraud
                return (base_score, "High Risk", base_explanations)
            elif signals >= 2:
                # 2 signals → Moderate risk
                reduced_score = 55.0
                return (
                    reduced_score,
                    "Medium Risk",
                    base_explanations + [
                        "",
                        "⚠️ CONFIDENCE ADJUSTMENT:",
                        f"   Only {signals} strong fraud signals detected",
                        f"   Score reduced: {base_score:.1f} → {reduced_score:.1f}",
                        "   Requires more evidence for HIGH RISK classification",
                    ]
                )
            else:
                # 0-1 signals → Low confidence
                reduced_score = 35.0
                return (
                    reduced_score,
                    "Medium Risk",
                    base_explanations + [
                        "",
                        "⚠️ LOW CONFIDENCE:",
                        f"   Only {signals} fraud signal detected",
                        f"   Score reduced: {base_score:.1f} → {reduced_score:.1f}",
                        "   May be false positive",
                    ]
                )
        
        # Default: return base detection
        return (base_score, base_category, base_explanations)
    
    def _count_risk_signals(self, features: Dict, explanations: List[str]) -> int:
        """
        Count number of strong fraud signals
        Used to prevent false positives
        """
        signals = 0
        
        # Signal 1: On blacklist
        if any('BLACKLIST' in exp for exp in explanations):
            signals += 1
        
        # Signal 2: Scam patterns
        if any('SCAM PATTERN' in exp for exp in explanations):
            signals += 1
        
        # Signal 3: Distribution patterns
        if any('DISTRIBUTION' in exp for exp in explanations):
            signals += 1
        
        # Signal 4: Drained account
        if any('DRAINED' in exp for exp in explanations):
            signals += 1
        
        # Signal 5: Very new with admin controls
        age_mins = features.get('Time Diff between first and last (Mins)', 0)
        age_days = age_mins / 1440 if age_mins > 0 else 0
        has_admin = features.get('can_mint', 0) > 0 or features.get('can_pause', 0) > 0
        
        if age_days < 30 and has_admin:
            signals += 1
        
        # Signal 6: Very low liquidity with admin controls
        liquidity = features.get('total_liquidity_usd', 0)
        if liquidity < 10000 and has_admin:
            signals += 1
        
        return signals
    
    def get_detection_summary(self, *args, **kwargs):
        """Pass through to base detector"""
        return self.base_detector.get_detection_summary(*args, **kwargs)
