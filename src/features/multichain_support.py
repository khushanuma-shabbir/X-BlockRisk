"""
Multi-Chain Support Module
Extends fraud detection to BSC, Polygon, Arbitrum, and other EVM chains.

Production Features:
- Chain selector UI
- Chain-specific API endpoints
- Unified risk scoring across chains
- Cross-chain transaction tracking
"""

import os
import requests
from typing import Dict, Tuple, Optional
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Chain(Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVALANCHE = "avalanche"
    FANTOM = "fantom"
    SOLANA = "solana"


# Chain-specific API configurations
CHAIN_CONFIG = {
    Chain.ETHEREUM: {
        'name': 'Ethereum Mainnet',
        'api_url': 'https://api.etherscan.io/api',
        'api_key_env': 'ETHERSCAN_API_KEY',
        'native_token': 'ETH',
        'chain_id': 1,
        'explorer': 'https://etherscan.io',
        'icon': '⟠'
    },
    Chain.BSC: {
        'name': 'BNB Smart Chain',
        'api_url': 'https://api.bscscan.com/api',
        'api_key_env': 'BSCSCAN_API_KEY',
        'native_token': 'BNB',
        'chain_id': 56,
        'explorer': 'https://bscscan.com',
        'icon': '🟡'
    },
    Chain.POLYGON: {
        'name': 'Polygon',
        'api_url': 'https://api.polygonscan.com/api',
        'api_key_env': 'POLYGONSCAN_API_KEY',
        'native_token': 'MATIC',
        'chain_id': 137,
        'explorer': 'https://polygonscan.com',
        'icon': '🟣'
    },
    Chain.ARBITRUM: {
        'name': 'Arbitrum One',
        'api_url': 'https://api.arbiscan.io/api',
        'api_key_env': 'ARBISCAN_API_KEY',
        'native_token': 'ETH',
        'chain_id': 42161,
        'explorer': 'https://arbiscan.io',
        'icon': '🔵'
    },
    Chain.OPTIMISM: {
        'name': 'Optimism',
        'api_url': 'https://api-optimistic.etherscan.io/api',
        'api_key_env': 'OPTIMISM_API_KEY',
        'native_token': 'ETH',
        'chain_id': 10,
        'explorer': 'https://optimistic.etherscan.io',
        'icon': '🔴'
    },
    Chain.AVALANCHE: {
        'name': 'Avalanche C-Chain',
        'api_url': 'https://api.snowtrace.io/api',
        'api_key_env': 'SNOWTRACE_API_KEY',
        'native_token': 'AVAX',
        'chain_id': 43114,
        'explorer': 'https://snowtrace.io',
        'icon': '🔺'
    },
    Chain.FANTOM: {
        'name': 'Fantom Opera',
        'api_url': 'https://api.ftmscan.com/api',
        'api_key_env': 'FTMSCAN_API_KEY',
        'native_token': 'FTM',
        'chain_id': 250,
        'explorer': 'https://ftmscan.com',
        'icon': '👻'
    },
    Chain.SOLANA: {
        'name': 'Solana',
        'api_url': None,  # Uses Helius/QuickNode
        'api_key_env': 'HELIUS_API_KEY',
        'native_token': 'SOL',
        'chain_id': None,
        'explorer': 'https://solscan.io',
        'icon': '🌐'
    }
}


class MultiChainAnalyzer:
    """
    Multi-chain fraud detection analyzer
    """
    
    def __init__(self):
        """Initialize multi-chain analyzer with API keys"""
        self.chain_configs = CHAIN_CONFIG
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[Chain, str]:
        """Load API keys from environment"""
        keys = {}
        
        for chain, config in self.chain_configs.items():
            key_env = config.get('api_key_env')
            if key_env:
                api_key = os.getenv(key_env, '')
                if api_key:
                    keys[chain] = api_key
                    logger.info(f"✓ Loaded API key for {config['name']}")
                else:
                    logger.warning(f"⚠ Missing API key for {config['name']} ({key_env})")
        
        return keys
    
    def get_available_chains(self) -> list:
        """
        Get list of chains with configured API keys
        
        Returns:
            list of (Chain, config_dict) tuples
        """
        available = []
        
        for chain, config in self.chain_configs.items():
            if chain in self.api_keys or chain == Chain.SOLANA:
                available.append((chain, config))
        
        return available
    
    def detect_chain(self, address: str) -> Optional[Chain]:
        """
        Auto-detect blockchain from address format
        
        Args:
            address: Wallet address
        
        Returns:
            Chain enum or None
        """
        address = address.strip()
        
        # Solana addresses (base58, 32-44 chars)
        if len(address) >= 32 and len(address) <= 44 and not address.startswith('0x'):
            return Chain.SOLANA
        
        # EVM addresses (0x + 40 hex chars)
        elif address.startswith('0x') and len(address) == 42:
            # Can't distinguish between EVM chains by address alone
            # Default to Ethereum
            return Chain.ETHEREUM
        
        return None
    
    def fetch_wallet_data(
        self, 
        address: str, 
        chain: Chain
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch wallet data from specified chain
        
        Args:
            address: Wallet address
            chain: Blockchain network
        
        Returns:
            (data_dict, error_message)
        """
        config = self.chain_configs.get(chain)
        
        if not config:
            return None, f"Chain {chain} not supported"
        
        # Check API key
        if chain not in self.api_keys and chain != Chain.SOLANA:
            return None, f"No API key configured for {config['name']}"
        
        # Solana uses different API
        if chain == Chain.SOLANA:
            return self._fetch_solana_data(address)
        
        # EVM chains use Etherscan-like APIs
        return self._fetch_evm_data(address, chain)
    
    def _fetch_evm_data(
        self, 
        address: str, 
        chain: Chain
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch data from EVM-compatible chain
        
        Args:
            address: Wallet address
            chain: EVM chain
        
        Returns:
            (data_dict, error_message)
        """
        config = self.chain_configs[chain]
        api_key = self.api_keys.get(chain)
        api_url = config['api_url']
        
        try:
            # Get normal transactions
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': 10000,
                'sort': 'asc',
                'apikey': api_key
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') != '1':
                return None, f"API error: {data.get('message', 'Unknown error')}"
            
            txs = data.get('result', [])
            
            # Get token transfers
            params['action'] = 'tokentx'
            response = requests.get(api_url, params=params, timeout=10)
            token_data = response.json()
            
            token_txs = token_data.get('result', []) if token_data.get('status') == '1' else []
            
            logger.info(
                f"✓ Fetched {len(txs)} normal txs + {len(token_txs)} token txs "
                f"from {config['name']}"
            )
            
            return {
                'transactions': txs,
                'token_transactions': token_txs,
                'chain': chain.value,
                'native_token': config['native_token'],
                'explorer': config['explorer']
            }, None
        
        except requests.exceptions.Timeout:
            return None, f"{config['name']} API timeout"
        except Exception as e:
            return None, f"Error fetching data: {str(e)}"
    
    def _fetch_solana_data(
        self, 
        address: str
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch data from Solana
        
        Note: Requires Helius or QuickNode API
        """
        # Placeholder - integrate with existing Solana module
        from ..live.fetch_solana import fetch_solana_pool
        
        try:
            features = fetch_solana_pool(address)
            
            if features:
                return {
                    'features': features,
                    'chain': 'solana',
                    'native_token': 'SOL',
                    'explorer': 'https://solscan.io'
                }, None
            else:
                return None, "No data found for Solana address"
        
        except Exception as e:
            return None, f"Solana fetch error: {str(e)}"
    
    def get_chain_info(self, chain: Chain) -> Dict:
        """Get configuration info for a chain"""
        return self.chain_configs.get(chain, {})
    
    def format_explorer_link(self, address: str, chain: Chain) -> str:
        """
        Generate block explorer link for address
        
        Args:
            address: Wallet/contract address
            chain: Blockchain network
        
        Returns:
            Full explorer URL
        """
        config = self.chain_configs.get(chain)
        
        if not config:
            return address
        
        explorer = config['explorer']
        
        if chain == Chain.SOLANA:
            return f"{explorer}/account/{address}"
        else:
            return f"{explorer}/address/{address}"


def get_chain_selector_options() -> list:
    """
    Get chain options for UI selector
    
    Returns:
        list of (display_name, chain_enum) tuples
    """
    analyzer = MultiChainAnalyzer()
    available = analyzer.get_available_chains()
    
    options = []
    for chain, config in available:
        display_name = f"{config['icon']} {config['name']} ({config['native_token']})"
        options.append((display_name, chain))
    
    return options


# Example usage
if __name__ == '__main__':
    print("Multi-Chain Support Module")
    print("="*60)
    
    analyzer = MultiChainAnalyzer()
    
    print("\nAvailable Chains:")
    for chain, config in analyzer.get_available_chains():
        print(f"  {config['icon']} {config['name']} ({config['native_token']})")
    
    print("\nChain Detection Examples:")
    test_addresses = [
        '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',  # EVM
        '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU'  # Solana
    ]
    
    for addr in test_addresses:
        detected = analyzer.detect_chain(addr)
        print(f"  {addr[:20]}... → {detected.value if detected else 'Unknown'}")
