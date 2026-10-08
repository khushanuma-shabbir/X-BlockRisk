"""
Machine Learning module for fraud detection

Contains:
- collect_ethereum_training_data.py: Scrapes labeled Ethereum addresses
- lightweight_fraud_detector.py: Random Forest model trained on Ethereum data
"""

from .lightweight_fraud_detector import LightweightFraudDetector
from .collect_ethereum_training_data import EthereumDataCollector

__all__ = ['LightweightFraudDetector', 'EthereumDataCollector']
