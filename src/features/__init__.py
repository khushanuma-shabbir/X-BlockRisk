"""
Production Features Module
Enterprise-grade features for billion-dollar fraud detection system.

Task #4: Feature Layer
- Batch Analysis: CSV upload/download, parallel processing
- Multi-chain Support: BSC, Polygon, Arbitrum, etc.
- User History: Search tracking, watchlist, trend analysis
- Contract Scanner: Rule-based smart contract risk assessment
"""

from .batch_analyzer import BatchAnalyzer, create_batch_template
from .multichain_support import MultiChainAnalyzer, Chain, get_chain_selector_options
from .user_history import UserHistory

__all__ = [
    'BatchAnalyzer',
    'create_batch_template',
    'MultiChainAnalyzer',
    'Chain',
    'get_chain_selector_options',
    'UserHistory'
]
