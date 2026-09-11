"""
Smart Contract Risk Analysis Module

Rule-based risk assessment for Ethereum smart contracts.
Analyzes contract source code for common risk patterns.

Note: This is NOT an ML-based model. It uses heuristic rules
to identify suspicious patterns in verified contract source code.
"""

from .analyzer import analyze_contract, get_contract_risk_score

__all__ = ['analyze_contract', 'get_contract_risk_score']
