"""
Professional-Grade Analysis Engine
Transforms raw detection data into actionable insights
"""

from typing import Dict, List, Tuple
import datetime


class ProfessionalAnalyzer:
    """
    Generates professional-grade insights from fraud detection data
    """
    
    # Classification thresholds (lowered from 40 to 30)
    FRAUD_THRESHOLD = 30  # ≥30 = potential fraud
    HIGH_RISK_THRESHOLD = 70  # ≥70 = high risk
    
    @staticmethod
    def classify_address_type(features: Dict[str, float], is_contract: bool) -> str:
        """Determine what type of address this is"""
        
        if not is_contract:
            # Check transaction patterns for EOA
            sent = features.get('Sent tnx', 0)
            received = features.get('Received Tnx', 0)
            
            if sent == 0 and received > 0:
                return "Collector Wallet (Only receives funds)"
            elif sent > 0 and received == 0:
                return "Sender Wallet (Only sends funds)"
            elif sent > 100 and received > 100:
                return "Active Trading Wallet"
            elif sent < 10 and received < 10:
                return "Inactive/New Wallet"
            else:
                return "Regular Wallet"
        else:
            # Contract classification
            has_token = features.get('ERC20_total_tokens_count', 0) > 0
            has_liquidity = features.get('total_liquidity_usd', 0) > 0
            
            if has_token and has_liquidity:
                return "DeFi Token Contract"
            elif has_token:
                return "ERC-20 Token Contract"
            elif has_liquidity:
                return "Liquidity Pool"
            else:
                return "Smart Contract"
    
    @staticmethod
    def get_establishment_status(features: Dict[str, float]) -> Tuple[str, str]:
        """
        Determine if address is established or new
        
        Returns:
            (status, explanation)
        """
        age_mins = features.get('Time Diff between first and last (Mins)', 0)
        age_days = age_mins / 1440 if age_mins > 0 else 0
        liquidity = features.get('total_liquidity_usd', 0)
        
        if liquidity >= 5_000_000 and age_days >= 365:
            return "ESTABLISHED", f"${liquidity:,.0f} liquidity, {age_days:.0f} days old"
        elif liquidity >= 1_000_000 and age_days >= 180:
            return "MATURE", f"${liquidity:,.0f} liquidity, {age_days:.0f} days old"
        elif age_days >= 90:
            return "MODERATE", f"{age_days:.0f} days old"
        elif age_days >= 30:
            return "NEW", f"{age_days:.0f} days old (recent)"
        else:
            return "VERY NEW", f"{age_days:.0f} days old (high risk period)"
    
    @staticmethod
    def analyze_transaction_behavior(features: Dict[str, float]) -> List[str]:
        """Deep analysis of transaction patterns"""
        insights = []
        
        sent = features.get('Sent tnx', 0)
        received = features.get('Received Tnx', 0)
        unique_sent = features.get('Unique Sent To Addresses', 0)
        unique_received = features.get('Unique Received From Addresses', 0)
        total_sent_value = features.get('total Ether sent', 0)
        total_received_value = features.get('total ether received', 0)
        balance = features.get('total ether balance', 0)
        
        # Transaction volume analysis
        total_txs = sent + received
        if total_txs > 1000:
            insights.append(f"📊 High Activity: {int(total_txs)} transactions (very active address)")
        elif total_txs > 100:
            insights.append(f"📊 Moderate Activity: {int(total_txs)} transactions")
        elif total_txs > 0:
            insights.append(f"📊 Low Activity: {int(total_txs)} transactions")
        
        # Flow balance
        if total_received_value > 0:
            flow_ratio = total_sent_value / total_received_value
            if 0.9 <= flow_ratio <= 1.1:
                insights.append(f"💰 Balanced Flow: Sent {flow_ratio:.2f}x what was received (normal trading)")
            elif flow_ratio > 1.5:
                insights.append(f"⚠️ High Outflow: Sending {flow_ratio:.2f}x more than receiving")
            elif flow_ratio < 0.5:
                insights.append(f"📥 High Inflow: Receiving {1/flow_ratio:.2f}x more than sending (accumulation)")
        
        # Balance analysis
        if total_received_value > 0:
            balance_ratio = balance / total_received_value
            if balance_ratio < 0.01:
                insights.append(f"🚨 Drained: Received {total_received_value:.2f} ETH but balance is {balance:.4f} ETH")
            elif balance_ratio < 0.1:
                insights.append(f"⚠️ Low Balance: Only {balance_ratio*100:.1f}% of received funds remain")
            elif balance_ratio > 0.8:
                insights.append(f"💎 Holder: Retaining {balance_ratio*100:.0f}% of received funds")
        
        # Distribution pattern
        if sent > 0:
            distribution_ratio = unique_sent / sent if sent > 0 else 0
            if distribution_ratio > 0.5:
                insights.append(f"🔀 Wide Distribution: Each transaction sent to different address (phishing pattern)")
            elif distribution_ratio < 0.1:
                insights.append(f"🔁 Concentrated: Repeatedly sends to same addresses (normal behavior)")
        
        # Counterparty diversity
        if unique_received > 0:
            diversity = unique_sent / unique_received if unique_received > 0 else 0
            if diversity > 5:
                insights.append(f"🚨 High Dispersion: Sends to {diversity:.1f}x more addresses than receives from (redistribution)")
            elif diversity > 2:
                insights.append(f"⚠️ Moderate Dispersion: Sends to {diversity:.1f}x more addresses")
        
        return insights
    
    @staticmethod
    def generate_risk_factors(features: Dict[str, float], final_score: float) -> List[Dict[str, str]]:
        """Generate specific risk factors with severity"""
        risk_factors = []
        
        sent = features.get('Sent tnx', 0)
        received = features.get('Received Tnx', 0)
        unique_sent = features.get('Unique Sent To Addresses', 0)
        balance = features.get('total ether balance', 0)
        total_received = features.get('total ether received', 0)
        
        # High send/receive ratio
        if received > 0:
            ratio = sent / received
            if ratio > 8:
                risk_factors.append({
                    "severity": "HIGH",
                    "type": "Scam Pattern",
                    "description": f"Sends {ratio:.1f}x more transactions than it receives",
                    "implication": "Typical of phishing addresses that collect and redistribute stolen funds",
                    "action": "AVOID - High likelihood of scam"
                })
            elif ratio > 5:
                risk_factors.append({
                    "severity": "MEDIUM",
                    "type": "Distribution Pattern",
                    "description": f"Sends {ratio:.1f}x more than receives",
                    "implication": "Could be legitimate business or potential redistribution of funds",
                    "action": "Verify legitimacy before interacting"
                })
        
        # Drained wallet
        if total_received > 1 and balance < 0.01:
            risk_factors.append({
                "severity": "CRITICAL",
                "type": "Drained Wallet",
                "description": f"Received {total_received:.2f} ETH but balance is {balance:.4f} ETH",
                "implication": "All funds were immediately withdrawn - typical exit scam behavior",
                "action": "DO NOT SEND FUNDS - Likely abandoned address"
            })
        
        # Wide distribution
        if unique_sent > 150:
            risk_factors.append({
                "severity": "HIGH",
                "type": "Mass Distribution",
                "description": f"Sends to {int(unique_sent)} different addresses",
                "implication": "Distributing stolen funds or airdrop scam",
                "action": "High risk - avoid interaction"
            })
        
        # Admin control risks
        if features.get('can_mint', 0) > 0:
            risk_factors.append({
                "severity": "MEDIUM",
                "type": "Unlimited Minting",
                "description": "Owner can create unlimited tokens",
                "implication": "Risk of token inflation and value dilution",
                "action": "Monitor owner wallet for minting activity"
            })
        
        if features.get('owner_can_withdraw', 0) > 0:
            risk_factors.append({
                "severity": "HIGH",
                "type": "Liquidity Control",
                "description": "Owner can withdraw liquidity",
                "implication": "Rug pull risk - owner can drain the pool",
                "action": "Only invest amounts you can afford to lose"
            })
        
        return risk_factors
    
    @staticmethod
    def generate_recommendations(
        features: Dict[str, float],
        final_score: float,
        is_contract: bool,
        risk_factors: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if final_score >= ProfessionalAnalyzer.HIGH_RISK_THRESHOLD:
            # High risk
            recommendations.append("🚨 DO NOT INTERACT with this address")
            recommendations.append("❌ Do not send funds")
            recommendations.append("❌ Do not approve token spending")
            recommendations.append("📢 Report to Etherscan if you've been scammed")
            recommendations.append("🔍 Verify address on multiple block explorers")
            
        elif final_score >= ProfessionalAnalyzer.FRAUD_THRESHOLD:
            # Medium risk
            recommendations.append("⚠️ Exercise EXTREME CAUTION")
            recommendations.append("✓ Start with very small test transactions (<$10)")
            recommendations.append("✓ Verify contract source code if available")
            recommendations.append("✓ Check community feedback (Telegram, Discord, Twitter)")
            recommendations.append("✓ Use a burner wallet, not your main wallet")
            recommendations.append("❌ Avoid large investments until risk is clarified")
            
            if is_contract:
                recommendations.append("✓ Check if contract is verified on Etherscan")
                recommendations.append("✓ Look for audit reports from reputable firms")
        
        else:
            # Low risk
            recommendations.append("✅ Appears relatively safe for interaction")
            
            if is_contract:
                liquidity = features.get('total_liquidity_usd', 0)
                if liquidity > 0:
                    recommendations.append(f"💰 Current liquidity: ${liquidity:,.0f}")
                    
                    if liquidity < 100_000:
                        recommendations.append("⚠️ Low liquidity - high slippage risk on large trades")
                        recommendations.append("✓ Set slippage tolerance to 5-10%")
                    
                recommendations.append("✓ Start with small amounts to verify functionality")
                recommendations.append("✓ Check for any admin controls (mint, pause, blacklist)")
                recommendations.append("✓ Monitor owner wallet for suspicious activity")
            else:
                recommendations.append("✓ Standard wallet security practices apply")
                recommendations.append("✓ Verify recipient address carefully before sending")
        
        # Add general best practices
        recommendations.append("")
        recommendations.append("📚 General Best Practices:")
        recommendations.append("• Always verify addresses on multiple sources")
        recommendations.append("• Never share your private keys or seed phrase")
        recommendations.append("• Use hardware wallet for large amounts")
        recommendations.append("• Keep track of all transactions")
        
        return recommendations
    
    @staticmethod
    def get_comparable_addresses(final_score: float, is_contract: bool) -> List[Dict[str, str]]:
        """Suggest comparable addresses for context"""
        comparables = []
        
        if final_score >= 70:
            # High risk - compare to known scams
            comparables.append({
                "name": "Similar Risk Profile",
                "addresses": "Known phishing and scam addresses",
                "behavior": "High distribution, drained wallets, exit scams"
            })
        elif final_score >= 30:
            # Medium risk - mixed signals
            comparables.append({
                "name": "Similar Risk Profile",
                "addresses": "New/unverified projects with admin controls",
                "behavior": "Active but lacks trust signals"
            })
        else:
            # Low risk - compare to legitimate addresses
            if is_contract:
                comparables.append({
                    "name": "Similar to Established DeFi",
                    "examples": ["USDT (0xdAC17F958...)", "USDC (0xA0b86991...)", "WETH (0xC02aaA39...)"],
                    "behavior": "High liquidity, verified contracts, established reputation"
                })
            else:
                comparables.append({
                    "name": "Similar to Regular Wallets",
                    "examples": ["Exchange wallets", "Individual trader wallets"],
                    "behavior": "Normal trading patterns, balanced flow"
                })
        
        return comparables
    
    @staticmethod
    def generate_professional_report(
        address: str,
        features: Dict[str, float],
        final_score: float,
        category: str,
        explanations: List[str],
        is_contract: bool
    ) -> Dict:
        """
        Generate complete professional analysis report
        
        Returns:
            Complete analysis with all insights
        """
        
        # Classify address type
        address_type = ProfessionalAnalyzer.classify_address_type(features, is_contract)
        
        # Get establishment status
        establishment, establishment_info = ProfessionalAnalyzer.get_establishment_status(features)
        
        # Analyze transaction behavior
        behavioral_insights = ProfessionalAnalyzer.analyze_transaction_behavior(features)
        
        # Generate risk factors
        risk_factors = ProfessionalAnalyzer.generate_risk_factors(features, final_score)
        
        # Generate recommendations
        recommendations = ProfessionalAnalyzer.generate_recommendations(
            features, final_score, is_contract, risk_factors
        )
        
        # Get comparable addresses
        comparables = ProfessionalAnalyzer.get_comparable_addresses(final_score, is_contract)
        
        # Build financial profile
        financial_profile = {
            "balance": features.get('total ether balance', 0),
            "total_received": features.get('total ether received', 0),
            "total_sent": features.get('total Ether sent', 0),
            "avg_received": features.get('avg val received', 0),
            "avg_sent": features.get('avg val sent', 0),
            "unique_senders": features.get('Unique Received From Addresses', 0),
            "unique_receivers": features.get('Unique Sent To Addresses', 0),
        }
        
        # Time analysis
        age_mins = features.get('Time Diff between first and last (Mins)', 0)
        age_days = age_mins / 1440 if age_mins > 0 else 0
        
        return {
            "summary": {
                "address": address,
                "type": address_type,
                "risk_score": final_score,
                "category": category,
                "establishment": establishment,
                "establishment_info": establishment_info,
                "is_contract": is_contract,
                "age_days": age_days,
            },
            "financial_profile": financial_profile,
            "behavioral_insights": behavioral_insights,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "comparables": comparables,
            "raw_explanations": explanations,
            "detection_layers": {
                "threshold_used": ProfessionalAnalyzer.FRAUD_THRESHOLD,
                "fraud_threshold": f"Score ≥ {ProfessionalAnalyzer.FRAUD_THRESHOLD} flagged as potential fraud",
                "high_risk_threshold": f"Score ≥ {ProfessionalAnalyzer.HIGH_RISK_THRESHOLD} flagged as high risk",
            }
        }


# Example usage
if __name__ == '__main__':
    # Test with known phishing address
    test_features = {
        'Sent tnx': 908,
        'Received Tnx': 92,
        'Unique Sent To Addresses': 188,
        'Unique Received From Addresses': 33,
        'total Ether sent': 4756526.33,
        'total ether received': 6752538.40,
        'total ether balance': 1996012.07,
        'avg val sent': 5238.47,
        'avg val received': 73397.16,
        'Time Diff between first and last (Mins)': 1701358.28,
        'can_mint': 0,
        'owner_can_withdraw': 0,
    }
    
    analyzer = ProfessionalAnalyzer()
    report = analyzer.generate_professional_report(
        address="0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8",
        features=test_features,
        final_score=70.0,
        category="High Risk",
        explanations=["Test explanation"],
        is_contract=False
    )
    
    print("="*80)
    print("PROFESSIONAL ANALYSIS REPORT")
    print("="*80)
    print(f"\nAddress: {report['summary']['address']}")
    print(f"Type: {report['summary']['type']}")
    print(f"Risk Score: {report['summary']['risk_score']}/100")
    print(f"Category: {report['summary']['category']}")
    print(f"Establishment: {report['summary']['establishment']}")
    print(f"Age: {report['summary']['age_days']:.0f} days")
    
    print(f"\n💰 Financial Profile:")
    print(f"  Balance: {report['financial_profile']['balance']:.4f} ETH")
    print(f"  Total Received: {report['financial_profile']['total_received']:.2f} ETH")
    print(f"  Total Sent: {report['financial_profile']['total_sent']:.2f} ETH")
    
    print(f"\n🔍 Behavioral Insights:")
    for insight in report['behavioral_insights']:
        print(f"  {insight}")
    
    print(f"\n🚨 Risk Factors ({len(report['risk_factors'])}):")
    for rf in report['risk_factors']:
        print(f"  [{rf['severity']}] {rf['type']}")
        print(f"      {rf['description']}")
        print(f"      Action: {rf['action']}")
    
    print(f"\n💡 Recommendations ({len(report['recommendations'])}):")
    for rec in report['recommendations'][:5]:
        print(f"  {rec}")
