"""
Context-Aware Fraud Analysis
Provides TRUTHFUL, genuine insights based on real-world context
"""

from typing import Dict, List, Tuple


class ContextAwareAnalyzer:
    """
    Provides genuine, context-aware fraud analysis
    Understands the difference between major tokens and scams
    """
    
    # Major verified tokens - provide positive context
    MAJOR_TOKENS = {
        '0xdac17f958d2ee523a2206206994597c13d831ec7': {
            'name': 'Tether (USDT)',
            'type': 'USD Stablecoin',
            'rank': 3,
            'market_cap': '120B+',
            'description': 'Most widely used stablecoin, issued by Tether Ltd',
            'trust_level': 'VERY_HIGH',
        },
        '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': {
            'name': 'USD Coin (USDC)',
            'type': 'USD Stablecoin', 
            'rank': 5,
            'market_cap': '50B+',
            'description': 'Fully regulated stablecoin by Circle/Coinbase',
            'trust_level': 'VERY_HIGH',
        },
        '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': {
            'name': 'Wrapped Ether (WETH)',
            'type': 'Wrapped ETH',
            'rank': 10,
            'market_cap': '30B+',
            'description': 'ERC-20 wrapper for ETH, required for DeFi',
            'trust_level': 'VERY_HIGH',
        },
    }
    
    @staticmethod
    def analyze_with_context(
        address: str,
        final_score: float,
        features: Dict[str, float],
        is_contract: bool,
        explanations: List[str]
    ) -> Dict:
        """
        Generate GENUINE, truthful analysis with proper context
        
        Returns complete analysis that makes sense in real world
        """
        address_lower = address.lower()
        
        # Extract key metrics
        liquidity = features.get('total_liquidity_usd', 0)
        age_mins = features.get('Time Diff between first and last (Mins)', 0)
        age_days = age_mins / 1440 if age_mins > 0 else 0
        total_txs = features.get('Sent tnx', 0) + features.get('Received Tnx', 0)
        
        # Admin controls
        has_mint = features.get('can_mint', 0) > 0
        has_blacklist = features.get('has_blacklist', 0) > 0
        has_pause = features.get('can_pause', 0) > 0
        
        # Determine context level
        is_major_token = address_lower in ContextAwareAnalyzer.MAJOR_TOKENS
        is_mega_established = liquidity >= 10_000_000_000 and age_days >= 730  # $10B+, 2+ years
        is_established = liquidity >= 1_000_000_000 and age_days >= 365  # $1B+, 1+ year
        is_significant = liquidity >= 100_000_000 and age_days >= 180  # $100M+, 6+ months
        
        # Build analysis
        analysis = {
            'risk_level': '',
            'summary': '',
            'token_info': None,
            'context_explanation': '',
            'admin_controls_explanation': [],
            'activity_explanation': '',
            'recommendations': [],
            'verdict': '',
        }
        
        # === MAJOR TOKEN (USDT, USDC, WETH) ===
        if is_major_token:
            token = ContextAwareAnalyzer.MAJOR_TOKENS[address_lower]
            
            analysis['risk_level'] = 'SAFE'
            analysis['token_info'] = {
                'name': token['name'],
                'type': token['type'],
                'rank': f"#{token['rank']} by market cap",
                'market_cap': token['market_cap'],
            }
            
            analysis['summary'] = (
                f"✅ VERIFIED MAJOR TOKEN: {token['name']}\n\n"
                f"This is one of the most widely used cryptocurrencies in the world. "
                f"Used by millions of people daily on major exchanges like Binance, Coinbase, and Kraken. "
                f"Market cap: ${token['market_cap']}. "
                f"The low risk score reflects the exceptional trust and track record."
            )
            
            analysis['context_explanation'] = (
                f"💡 Why This Token Has Admin Controls:\n\n"
                f"Major stablecoins like {token['name']} REQUIRE admin controls to operate legally:\n\n"
                f"• Minting/Burning: Needed to maintain the $1.00 peg (mint when demand increases, burn when decreases)\n"
                f"• Blacklisting: Required by regulators to freeze funds linked to illegal activity\n"
                f"• Pause Function: Security emergency response (has never been abused)\n\n"
                f"These are NOT red flags for established tokens - they're standard operating procedure. "
                f"Even USDC (fully regulated by Circle) has identical controls."
            )
            
            analysis['activity_explanation'] = (
                f"📊 High Transaction Activity is EXPECTED:\n\n"
                f"{token['name']} processes billions of dollars daily. "
                f"High transaction volume indicates legitimate widespread adoption, not suspicious activity. "
                f"This token is used for:\n"
                f"• Trading on exchanges\n"
                f"• DeFi protocols\n"
                f"• International transfers\n"
                f"• Business payments"
            )
            
            analysis['recommendations'] = [
                f"✅ {token['name']} is safe to use for its intended purposes",
                "✅ Widely accepted on all major exchanges and DeFi platforms",
                "✅ Has multi-year track record of responsible operation",
                "ℹ️ Always verify you're interacting with the correct contract address",
                "ℹ️ Be aware of regulatory risks with stablecoins (potential freezing if linked to illegal activity)",
            ]
            
            analysis['verdict'] = (
                f"🎯 VERDICT: SAFE - Major Trusted Token\n\n"
                f"{token['name']} is one of the safest addresses you can interact with in crypto. "
                f"Admin controls are NORMAL and REQUIRED for this type of token. "
                f"Used safely by millions of users worldwide every day."
            )
        
        # === MEGA ESTABLISHED ($10B+, 2+ years) ===
        elif is_mega_established:
            analysis['risk_level'] = 'VERY_LOW'
            
            analysis['summary'] = (
                f"✅ HIGHLY ESTABLISHED TOKEN\n\n"
                f"Massive liquidity: ${liquidity/1e9:.1f} billion\n"
                f"Operating history: {age_days:.0f} days ({age_days/365:.1f} years)\n"
                f"Transaction volume: {int(total_txs):,} transactions\n\n"
                f"This level of adoption and longevity indicates a legitimate, widely-trusted project. "
                f"Projects with this much at stake don't risk their reputation on scams."
            )
            
            analysis['context_explanation'] = (
                f"💡 Why Admin Controls Are Less Risky Here:\n\n"
                f"With ${liquidity/1e9:.1f} billion locked and {age_days/365:.1f} years of operation:\n\n"
                f"• Team has strong incentive NOT to rug pull (would destroy massive value)\n"
                f"• Long track record shows responsible use of admin powers\n"
                f"• Liquidity size makes it practically impossible to exit scam\n"
                f"• Project is likely known publicly with legal entities\n\n"
                f"Admin controls here are for legitimate purposes (upgrades, security), not scams."
            )
            
            analysis['recommendations'] = [
                "✅ Generally safe to interact with",
                "✅ Track record indicates responsible team",
                "ℹ️ Still verify through official channels (website, social media)",
                "ℹ️ For large investments, research the project team and audits",
            ]
            
            analysis['verdict'] = (
                f"🎯 VERDICT: VERY LOW RISK - Established Project\n\n"
                f"The size and longevity make this a trustworthy address. "
                f"Admin controls are standard for projects of this scale."
            )
        
        # === ESTABLISHED ($1B+, 1+ year) ===
        elif is_established:
            analysis['risk_level'] = 'LOW'
            
            analysis['summary'] = (
                f"✅ ESTABLISHED TOKEN\n\n"
                f"Significant liquidity: ${liquidity/1e6:.1f} million\n"
                f"Operating since: {age_days:.0f} days ago ({age_days/365:.1f} years)\n\n"
                f"This shows real adoption and has survived market cycles. "
                f"Admin controls should still be monitored but have been used responsibly so far."
            )
            
            analysis['recommendations'] = [
                "✅ Appears safe based on track record",
                "ℹ️ Verify project through multiple sources",
                "ℹ️ Check for any recent controversies",
                "⚠️ Monitor for unusual admin activity",
            ]
            
            analysis['verdict'] = "🎯 VERDICT: LOW RISK - Proven track record makes this relatively safe"
        
        # === SIGNIFICANT ($100M+, 6+ months) ===
        elif is_significant:
            analysis['risk_level'] = 'MODERATE'
            
            analysis['summary'] = (
                f"⚠️ MODERATE RISK - Growing Project\n\n"
                f"Liquidity: ${liquidity/1e6:.1f} million\n"
                f"Age: {age_days:.0f} days ({age_days/30:.1f} months)\n\n"
                f"Has some track record but not fully established yet. "
                f"Admin controls present higher risk than major tokens."
            )
            
            analysis['context_explanation'] = (
                f"⚠️ Admin Control Risks:\n\n"
                f"Unlike major tokens, this project doesn't have years of proven trustworthiness.\n"
                f"Admin powers COULD be used maliciously:\n\n"
                f"• Minting: Could create infinite supply, crashing price\n"
                f"• Blacklisting: Could freeze your wallet arbitrarily\n"
                f"• Pause: Could prevent selling at key moments\n\n"
                f"The ${liquidity/1e6:.1f}M liquidity provides SOME security, but not guaranteed."
            )
            
            analysis['recommendations'] = [
                "⚠️ Exercise caution - not fully established",
                "⚠️ Only invest amounts you can afford to lose",
                "✓ Research team and check if audited",
                "✓ Join community channels to monitor developments",
                "✓ Check if liquidity is locked",
            ]
            
            analysis['verdict'] = "🎯 VERDICT: MODERATE RISK - Proceed with caution and research"
        
        # === HIGH RISK (Score >= 70) ===
        elif final_score >= 70:
            analysis['risk_level'] = 'HIGH'
            
            analysis['summary'] = (
                f"🚨 HIGH RISK - Multiple Red Flags\n\n"
                f"This address shows patterns commonly associated with scams:\n"
                f"Score: {final_score:.0f}/100 (70+ is high risk)\n\n"
                f"DO NOT INTERACT unless you can verify legitimacy through multiple independent sources."
            )
            
            analysis['context_explanation'] = (
                f"🚨 Why This Is Dangerous:\n\n"
                f"Red flags detected include suspicious transaction patterns, "
                f"admin control combinations, or blacklist matches.\n\n"
                f"Common scam tactics:\n"
                f"• Honeypot (can buy but not sell)\n"
                f"• Rug pull (drain liquidity instantly)\n"
                f"• Pump and dump (coordinated price manipulation)\n"
                f"• Fake token (impersonates real project)"
            )
            
            analysis['recommendations'] = [
                "🚨 AVOID - High fraud indicators",
                "❌ DO NOT send funds",
                "❌ DO NOT approve token spending",
                "ℹ️ If you've interacted, revoke approvals immediately",
                "📢 Report to Etherscan if confirmed scam",
            ]
            
            analysis['verdict'] = "🎯 VERDICT: HIGH RISK - Strong recommendation to AVOID"
        
        # === MEDIUM RISK (Score 27-69) ===
        elif final_score >= 27:
            analysis['risk_level'] = 'MEDIUM'
            
            analysis['summary'] = (
                f"⚠️ CAUTION - Potential Risks Detected\n\n"
                f"Score: {final_score:.0f}/100\n"
                f"Liquidity: ${liquidity:,.0f}\n"
                f"Age: {age_days:.0f} days\n\n"
                f"Some concerning patterns found. Not confirmed fraud, but warrants careful verification."
            )
            
            analysis['context_explanation'] = (
                f"⚠️ Risk Factors:\n\n"
                f"This address shows suspicious patterns but isn't definitively a scam. Could be:\n"
                f"• New legitimate project (lacks track record)\n"
                f"• Small token with risky tokenomics\n"
                f"• Project with concerning admin controls\n"
                f"• Unusual transaction patterns that need explanation"
            )
            
            analysis['recommendations'] = [
                "⚠️ Exercise EXTREME caution",
                "✓ Research thoroughly before interacting",
                "✓ Start with very small test transaction (<$10)",
                "✓ Verify project website, social media, team",
                "✓ Check for audit reports",
                "✓ Look for community feedback",
                "❌ Avoid large investments",
            ]
            
            analysis['verdict'] = "🎯 VERDICT: MEDIUM RISK - Verify thoroughly before proceeding"
        
        # === LOW RISK (Score < 27) ===
        else:
            analysis['risk_level'] = 'LOW'
            
            analysis['summary'] = (
                f"✅ LOW RISK - No Major Red Flags\n\n"
                f"Score: {final_score:.0f}/100 (under 27 is low risk)\n\n"
                f"Our analysis didn't find major red flags. However, always practice safe crypto habits."
            )
            
            analysis['recommendations'] = [
                "✅ No major concerns detected",
                "ℹ️ Still verify addresses independently",
                "ℹ️ Start with small transactions to test",
                "ℹ️ Never invest more than you can afford to lose",
                "ℹ️ Keep funds in hardware wallet when possible",
            ]
            
            analysis['verdict'] = "🎯 VERDICT: LOW RISK - Appears generally safe, standard precautions apply"
        
        # Add admin control specifics if present
        if has_mint or has_blacklist or has_pause:
            if analysis['admin_controls_explanation']:
                # Already explained in context
                pass
            else:
                controls = []
                if has_mint:
                    controls.append("• Can mint tokens")
                if has_blacklist:
                    controls.append("• Can blacklist wallets")
                if has_pause:
                    controls.append("• Can pause trading")
                
                analysis['admin_controls_explanation'] = [
                    "🔐 Admin Controls Detected:",
                    *controls,
                ]
        
        return analysis


# For backwards compatibility
class ProfessionalAnalyzer(ContextAwareAnalyzer):
    """Alias for compatibility"""
    FRAUD_THRESHOLD = 27
    HIGH_RISK_THRESHOLD = 70
