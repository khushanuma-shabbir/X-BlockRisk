"""
Main Smart Contract Risk Analyzer
Coordinates source code fetching, pattern analysis, and risk scoring.
"""

from .etherscan_api import fetch_contract_source, fetch_contract_metadata
from .risk_patterns import analyze_all_patterns


def get_contract_risk_score(contract_address):
    """
    Analyze a smart contract and return risk score + explanation
    
    Args:
        contract_address: Ethereum contract address
    
    Returns:
        tuple: (risk_score, risk_category, red_flags, data_source)
        - risk_score: 0-100 (0=safe, 100=extremely risky)
        - risk_category: 'Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk'
        - red_flags: list of plain-English explanations
        - data_source: 'VERIFIED', 'UNVERIFIED', or 'ERROR'
    """
    print(f"\n{'='*60}")
    print(f"SMART CONTRACT RISK ANALYSIS")
    print(f"Contract: {contract_address}")
    print(f"{'='*60}")
    
    # Fetch contract data from Etherscan
    contract_data = fetch_contract_source(contract_address)
    
    # Check for errors
    if contract_data.get('error') and not contract_data.get('verified'):
        error_msg = contract_data.get('error')
        return 50, 'Unknown Risk', [
            f"Error fetching contract data: {error_msg}",
            "Unable to perform analysis without contract source code.",
            "⚠️ Proceed with caution when interacting with this contract."
        ], 'ERROR'
    
    # If unverified, that's a major red flag
    if not contract_data.get('verified'):
        return 75, 'High Risk', [
            "❌ Contract source code is NOT verified on Etherscan",
            "Without verified source code, the contract's actual behavior cannot be audited.",
            "This is a major red flag - legitimate projects typically verify their contracts.",
            "⚠️ HIGH RISK: Avoid interacting with unverified contracts."
        ], 'UNVERIFIED'
    
    # Contract is verified - analyze patterns
    print(f"[INFO] Analyzing verified contract: {contract_data.get('contract_name')}")
    patterns = analyze_all_patterns(contract_data)
    
    # Calculate total risk score
    base_score = 0  # Start neutral for verified contracts
    risk_adjustments = []
    positive_indicators = []
    
    for pattern in patterns:
        score_change = pattern['risk_score']
        
        if score_change > 0:
            # Risk indicator
            base_score += score_change
            risk_adjustments.append({
                'pattern': pattern['pattern'],
                'severity': pattern['severity'],
                'explanation': pattern['explanation'],
                'score': score_change
            })
        else:
            # Positive indicator
            base_score += score_change  # Add negative (reduces risk)
            positive_indicators.append({
                'pattern': pattern['pattern'],
                'explanation': pattern['explanation'],
                'score': score_change
            })
    
    # Cap score at 0-100
    final_score = max(0, min(100, base_score))
    
    # Determine risk category
    if final_score >= 70:
        risk_category = 'Critical Risk'
    elif final_score >= 50:
        risk_category = 'High Risk'
    elif final_score >= 30:
        risk_category = 'Medium Risk'
    else:
        risk_category = 'Low Risk'
    
    # Build explanation
    red_flags = []
    
    # Add contract info
    red_flags.append(f"✅ Contract verified: {contract_data.get('contract_name')}")
    red_flags.append(f"Compiler: {contract_data.get('compiler_version', 'Unknown')}")
    red_flags.append("")
    
    # Add risk patterns
    if risk_adjustments:
        red_flags.append("⚠️ RISK INDICATORS DETECTED:")
        for adj in sorted(risk_adjustments, key=lambda x: x['score'], reverse=True):
            severity_icon = "🔴" if adj['severity'] == 'CRITICAL' else "🟠" if adj['severity'] == 'HIGH' else "🟡"
            red_flags.append(f"{severity_icon} {adj['explanation']} (+{adj['score']} risk)")
        red_flags.append("")
    
    # Add positive indicators
    if positive_indicators:
        red_flags.append("✅ POSITIVE INDICATORS:")
        for pos in positive_indicators:
            red_flags.append(f"• {pos['explanation']}")
        red_flags.append("")
    
    # Add summary
    if final_score < 30:
        red_flags.append("📊 ASSESSMENT: This contract follows standard patterns with no major red flags detected.")
        red_flags.append("⚠️ Note: This is a rule-based analysis. Always do your own research (DYOR).")
    elif final_score < 50:
        red_flags.append("📊 ASSESSMENT: Some concerning patterns detected. Review carefully before interacting.")
        red_flags.append("⚠️ Recommendation: Verify project legitimacy and team background.")
    elif final_score < 70:
        red_flags.append("📊 ASSESSMENT: Multiple risk indicators present. High caution advised.")
        red_flags.append("🚨 Recommendation: Avoid unless you fully understand the risks.")
    else:
        red_flags.append("📊 ASSESSMENT: CRITICAL risk indicators detected.")
        red_flags.append("🚨 STRONG RECOMMENDATION: Do NOT interact with this contract.")
    
    print(f"[RESULT] Risk Score: {final_score}/100 ({risk_category})")
    print(f"[RESULT] Patterns detected: {len(patterns)}")
    
    return final_score, risk_category, red_flags, 'VERIFIED'


def analyze_contract(contract_address):
    """
    Wrapper function for backward compatibility
    Returns dict with all analysis results
    """
    risk_score, risk_category, explanations, data_source = get_contract_risk_score(contract_address)
    
    return {
        'risk_score': risk_score,
        'risk_category': risk_category,
        'explanations': explanations,
        'data_source': data_source,
        'address': contract_address
    }
