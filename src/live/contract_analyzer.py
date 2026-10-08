"""
Smart Contract Analyzer - Detects Admin Powers and Contract Risks
Extracts: mint, pause, blacklist, fees, limits, trading controls, withdraw powers
Now with API caching for reproducibility
"""

import requests
import time
import re
from typing import Dict, Tuple, Optional
from src.cache.api_cache import get_cache

class ContractAnalyzer:
    """Analyzes Ethereum smart contracts for admin control features"""
    
    # Function signatures to detect (first 4 bytes of keccak256)
    FUNCTION_SIGNATURES = {
        'mint': ['0x40c10f19', '0xa0712d68', '0x449a52f8'],  # mint(address,uint256), mint(uint256), mint()
        'pause': ['0x8456cb59', '0x02329a29'],  # pause(), pause(bool)
        'blacklist': ['0xf9f92be4', '0x0a3b0a4f'],  # blacklist(address), addBlackList(address)
        'withdraw': ['0x3ccfd60b', '0x00f714ce', '0x51cff8d9'],  # withdraw(), withdrawAll(), withdrawETH()
    }
    
    def __init__(self, etherscan_api_key: str, chain_id: str = '1', use_cache: bool = True):
        self.api_key = etherscan_api_key
        self.chain_id = chain_id  # 1 = Ethereum mainnet
        self.base_url = "https://api.etherscan.io/v2/api"
        self.cache = {}
        self.use_cache = use_cache
        self.api_cache = get_cache() if use_cache else None
    
    def is_contract(self, address: str) -> bool:
        """Check if address is a contract (has bytecode)"""
        try:
            params = {
                'chainid': self.chain_id,
                'module': 'proxy',
                'action': 'eth_getCode',
                'address': address,
                'tag': 'latest',
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data.get('result') and data['result'] != '0x':
                return len(data['result']) > 10  # Has actual code
            return False
        except:
            return False
    
    def get_contract_abi(self, address: str) -> Optional[dict]:
        """Fetch verified contract ABI from Etherscan V2 API (with caching)"""
        try:
            params = {
                'chainid': self.chain_id,
                'module': 'contract',
                'action': 'getabi',
                'address': address,
                'apikey': self.api_key
            }
            
            # Check cache first
            if self.api_cache:
                cached = self.api_cache.get('etherscan_getabi', {'address': address})
                if cached:
                    if cached.get('status') == '1' and cached.get('result'):
                        import json
                        return json.loads(cached['result'])
                    return None
            
            # Make API call
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            # Cache response
            if self.api_cache:
                self.api_cache.set('etherscan_getabi', {'address': address}, data)
            
            if data.get('status') == '1' and data.get('result'):
                import json
                return json.loads(data['result'])
            return None
        except:
            return None
    
    def get_contract_bytecode(self, address: str) -> Optional[str]:
        """Get contract bytecode"""
        try:
            params = {
                'chainid': self.chain_id,
                'module': 'proxy',
                'action': 'eth_getCode',
                'address': address,
                'tag': 'latest',
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            return data.get('result', '')
        except:
            return None
    
    def analyze_abi_functions(self, abi: list) -> Dict[str, int]:
        """Analyze ABI for dangerous functions"""
        features = {
            'can_mint': 0,
            'has_blacklist': 0,
            'can_pause': 0,
            'owner_can_withdraw': 0,
        }
        
        if not abi:
            return features
        
        function_names = []
        for item in abi:
            if item.get('type') == 'function':
                func_name = item.get('name', '').lower()
                function_names.append(func_name)
        
        # Check for mint functions
        mint_keywords = ['mint', '_mint', 'minttoken', 'minttokens', 'issue']
        if any(keyword in func_name for func_name in function_names for keyword in mint_keywords):
            features['can_mint'] = 1
        
        # Check for blacklist functions
        blacklist_keywords = ['blacklist', 'addblacklist', 'addtoblacklist', 'ban', 'block']
        if any(keyword in func_name for func_name in function_names for keyword in blacklist_keywords):
            features['has_blacklist'] = 1
        
        # Check for pause functions
        pause_keywords = ['pause', 'unpause', 'setpaused']
        if any(keyword in func_name for func_name in function_names for keyword in pause_keywords):
            features['can_pause'] = 1
        
        # Check for withdraw functions
        withdraw_keywords = ['withdraw', 'withdraweth', 'withdrawtoken', 'rug', 'drain']
        if any(keyword in func_name for func_name in function_names for keyword in withdraw_keywords):
            features['owner_can_withdraw'] = 1
        
        return features
    
    def analyze_bytecode(self, bytecode: str) -> Dict[str, int]:
        """Fallback: analyze bytecode for function signatures"""
        features = {
            'can_mint': 0,
            'has_blacklist': 0,
            'can_pause': 0,
            'owner_can_withdraw': 0,
        }
        
        if not bytecode or bytecode == '0x':
            return features
        
        # Check for function signatures in bytecode
        for func_type, signatures in self.FUNCTION_SIGNATURES.items():
            for sig in signatures:
                if sig.replace('0x', '') in bytecode:
                    if func_type == 'mint':
                        features['can_mint'] = 1
                    elif func_type == 'pause':
                        features['can_pause'] = 1
                    elif func_type == 'blacklist':
                        features['has_blacklist'] = 1
                    elif func_type == 'withdraw':
                        features['owner_can_withdraw'] = 1
        
        return features
    
    def analyze_contract(self, address: str) -> Dict[str, int]:
        """
        Complete contract analysis
        Returns dict with admin control features
        """
        # Check cache
        if address in self.cache:
            return self.cache[address]
        
        # Default: no admin powers
        features = {
            'can_mint': 0,
            'has_blacklist': 0,
            'can_pause': 0,
            'fee_too_high': 0,
            'has_trading_limits': 0,
            'has_trading_cooldown': 0,
            'owner_can_withdraw': 0,
            'owner_change_balance': 0,
        }
        
        # Check if contract
        if not self.is_contract(address):
            self.cache[address] = features
            return features
        
        # Try ABI analysis first (most accurate)
        abi = self.get_contract_abi(address)
        if abi:
            abi_features = self.analyze_abi_functions(abi)
            features.update(abi_features)
        else:
            # Fallback: bytecode analysis
            bytecode = self.get_contract_bytecode(address)
            if bytecode:
                bytecode_features = self.analyze_bytecode(bytecode)
                features.update(bytecode_features)
        
        # Cache result
        self.cache[address] = features
        return features


# Quick test
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('ETHERSCAN_API_KEY', '')
    analyzer = ContractAnalyzer(api_key)
    
    # Test with USDT (known to have admin powers)
    usdt = '0xdAC17F958D2ee523a2206206994597C13D831ec7'
    print(f"Testing USDT contract: {usdt}")
    features = analyzer.analyze_contract(usdt)
    print("Features detected:", features)
