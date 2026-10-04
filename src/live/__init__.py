"""
Live Data Fetching Module
Real-time blockchain data fetching with security and performance layers.
"""

from .fetch_ethereum import fetch_ethereum_wallet
from .fetch_solana import fetch_solana_pool

__all__ = ['fetch_ethereum_wallet', 'fetch_solana_pool']
