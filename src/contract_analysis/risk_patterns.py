"""
Risk Pattern Detection for Smart Contracts
Rule-based heuristics to identify suspicious patterns in contract source code.
"""

import re


def check_unverified_contract(contract_data):
    """Check if contract is verified"""
    if not contract_data.get('verified'):
        return {
            'risk_score': 40,
            'pattern': 'UNVERIFIED_CONTRACT',
            'severity': 'HIGH',
            'explanation': 'Contract source code is not verified on Etherscan. This is a major red flag as the actual contract behavior cannot be audited.'
        }
    return None


def check_mint_functions(source_code):
    """Check for unrestricted mint functions"""
    if not source_code:
        return None
    
    # Look for mint functions
    mint_pattern = r'function\s+mint\s*\([^)]*\)'
    mint_matches = re.findall(mint_pattern, source_code, re.IGNORECASE)
    
    if mint_matches:
        # Check if there are access controls (onlyOwner, require, etc.)
        has_owner_check = bool(re.search(r'onlyOwner|require.*msg\.sender|modifier.*owner', source_code, re.IGNORECASE))
        
        if not has_owner_check:
            return {
                'risk_score': 35,
                'pattern': 'UNRESTRICTED_MINT',
                'severity': 'HIGH',
                'explanation': f'Found {len(mint_matches)} mint function(s) with no clear access control. This allows unlimited token creation, leading to inflation.'
            }
        else:
            return {
                'risk_score': 10,
                'pattern': 'CONTROLLED_MINT',
                'severity': 'LOW',
                'explanation': f'Found {len(mint_matches)} mint function(s) with owner access control. Standard pattern for managed tokens.'
            }
    
    return None


def check_ownership_controls(source_code):
    """Check for owner withdrawal/control functions"""
    if not source_code:
        return None
    
    risk_functions = []
    
    # Withdraw functions
    withdraw_pattern = r'function\s+withdraw\s*\([^)]*\)'
    if re.search(withdraw_pattern, source_code, re.IGNORECASE):
        risk_functions.append('withdraw')
    
    # Transfer ownership without proper checks
    transfer_pattern = r'function\s+transferOwnership\s*\([^)]*\)'
    if re.search(transfer_pattern, source_code, re.IGNORECASE):
        risk_functions.append('transferOwnership')
    
    # Drain/rug functions (explicit scam indicators)
    if re.search(r'function.*(drain|rug|sweep|rescue).*\(', source_code, re.IGNORECASE):
        return {
            'risk_score': 50,
            'pattern': 'SUSPICIOUS_DRAIN_FUNCTION',
            'severity': 'CRITICAL',
            'explanation': 'Contract contains functions with names like "drain", "rug", or "sweep" - explicit scam indicators.'
        }
    
    if len(risk_functions) >= 2:
        return {
            'risk_score': 25,
            'pattern': 'MULTIPLE_OWNER_CONTROLS',
            'severity': 'MEDIUM',
            'explanation': f'Contract has multiple owner-controlled functions: {", ".join(risk_functions)}. High owner privileges increase rug-pull risk.'
        }
    
    return None


def check_honeypot_patterns(source_code):
    """Check for honeypot indicators (pause, blacklist, etc.)"""
    if not source_code:
        return None
    
    honeypot_indicators = []
    
    # Pause functionality
    if re.search(r'function\s+pause|whenNotPaused|_pause\(', source_code, re.IGNORECASE):
        honeypot_indicators.append('pause mechanism')
    
    # Blacklist functionality
    if re.search(r'blacklist|isBlacklisted|_blacklist', source_code, re.IGNORECASE):
        honeypot_indicators.append('blacklist')
    
    # Transfer restrictions
    if re.search(r'canTransfer|transferAllowed|_beforeTransfer.*require', source_code, re.IGNORECASE):
        honeypot_indicators.append('transfer restrictions')
    
    # High tax/fee patterns (>10%)
    if re.search(r'(tax|fee).*=.*[1-9][0-9]', source_code, re.IGNORECASE):
        honeypot_indicators.append('high tax/fee')
    
    if len(honeypot_indicators) >= 2:
        return {
            'risk_score': 35,
            'pattern': 'HONEYPOT_INDICATORS',
            'severity': 'HIGH',
            'explanation': f'Multiple honeypot indicators detected: {", ".join(honeypot_indicators)}. These can prevent selling after buying.'
        }
    elif len(honeypot_indicators) == 1:
        return {
            'risk_score': 15,
            'pattern': 'SINGLE_RESTRICTION',
            'severity': 'MEDIUM',
            'explanation': f'Found {honeypot_indicators[0]} - common in legitimate tokens but can be abused.'
        }
    
    return None


def check_proxy_patterns(source_code):
    """Check for proxy/upgradeable contract patterns"""
    if not source_code:
        return None
    
    # Check for proxy patterns
    proxy_indicators = []
    
    if re.search(r'delegatecall|Proxy|upgradeable|UUPS', source_code, re.IGNORECASE):
        proxy_indicators.append('proxy/upgradeable')
    
    if re.search(r'implementation.*slot|_IMPLEMENTATION', source_code, re.IGNORECASE):
        proxy_indicators.append('implementation slot')
    
    if proxy_indicators:
        return {
            'risk_score': 20,
            'pattern': 'UPGRADEABLE_CONTRACT',
            'severity': 'MEDIUM',
            'explanation': f'Contract appears to be upgradeable ({", ".join(proxy_indicators)}). Owner can change contract logic after deployment.'
        }
    
    return None


def check_ownership_renounced(source_code):
    """Check if ownership has been renounced"""
    if not source_code:
        return None
    
    # Check for renounceOwnership function
    if re.search(r'function\s+renounceOwnership', source_code, re.IGNORECASE):
        # This is actually GOOD - means ownership CAN be renounced
        return {
            'risk_score': -10,  # Negative = reduces risk
            'pattern': 'RENOUNCEABLE_OWNERSHIP',
            'severity': 'POSITIVE',
            'explanation': 'Contract includes renounceOwnership function - allows owner to give up control, reducing rug-pull risk.'
        }
    
    return None


def check_standard_interfaces(source_code):
    """Check if contract follows standard interfaces (ERC20, ERC721, etc.)"""
    if not source_code:
        return None
    
    standards = []
    
    if re.search(r'ERC20|IERC20|totalSupply.*balanceOf.*transfer', source_code, re.IGNORECASE):
        standards.append('ERC20')
    
    if re.search(r'ERC721|IERC721|ownerOf.*tokenURI', source_code, re.IGNORECASE):
        standards.append('ERC721')
    
    if re.search(r'ERC1155|IERC1155', source_code, re.IGNORECASE):
        standards.append('ERC1155')
    
    if standards:
        return {
            'risk_score': -5,  # Negative = reduces risk
            'pattern': 'STANDARD_INTERFACE',
            'severity': 'POSITIVE',
            'explanation': f'Contract implements standard interface(s): {", ".join(standards)}. Follows established patterns.'
        }
    
    return None


def analyze_all_patterns(contract_data):
    """
    Run all risk pattern checks
    
    Returns:
        list of detected patterns with risk scores
    """
    source_code = contract_data.get('source_code', '')
    patterns = []
    
    # Check each pattern
    checks = [
        check_unverified_contract(contract_data),
        check_mint_functions(source_code),
        check_ownership_controls(source_code),
        check_honeypot_patterns(source_code),
        check_proxy_patterns(source_code),
        check_ownership_renounced(source_code),
        check_standard_interfaces(source_code)
    ]
    
    # Collect non-None results
    for check_result in checks:
        if check_result:
            patterns.append(check_result)
    
    return patterns
