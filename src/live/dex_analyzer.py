"""
DEX Analyzer - Fetches Liquidity and Token Age
Uses CoinGecko API (free tier) as primary data source
Provides context data for admin-control risk adjustment
Now with API caching for reproducibility
"""

import requests
import time
from typing import Dict, Optional
from datetime import datetime
from src.cache.api_cache import get_cache

class DexAnalyzer:
    """Analyzes token liquidity and age using CoinGecko"""
    
    def __init__(self, etherscan_api_key: Optional[str] = None, use_cache: bool = True):
        # CoinGecko for market data (free tier)
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        # Etherscan for contract creation date
        self.etherscan_api_key = etherscan_api_key
        self.etherscan_url = "https://api.etherscan.io/v2/api"
        self.cache = {}
        self.rate_limit_wait = 2  # seconds between requests
        self.use_cache = use_cache
        self.api_cache = get_cache() if use_cache else None
    
    def get_token_market_data(self, token_address: str) -> Dict[str, float]:
        """Get token market data from CoinGecko (with caching)"""
        try:
            # Check cache first
            if self.api_cache:
                cached = self.api_cache.get('coingecko_contract', {'address': token_address.lower()})
                if cached:
                    market_data = cached.get('market_data', {})
                    market_cap = market_data.get('market_cap', {}).get('usd', 0)
                    volume_24h = market_data.get('total_volume', {}).get('usd', 0)
                    liquidity_usd = market_cap
                    
                    genesis_date = cached.get('genesis_date')
                    age_days = 0
                    if genesis_date:
                        try:
                            genesis_dt = datetime.strptime(genesis_date, '%Y-%m-%d')
                            age_days = (datetime.now() - genesis_dt).days
                        except:
                            pass
                    
                    return {
                        'liquidity_usd': liquidity_usd,
                        'age_days': age_days,
                        'volume_24h': volume_24h
                    }
            
            # Make API call
            url = f"{self.coingecko_url}/coins/ethereum/contract/{token_address.lower()}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache response
                if self.api_cache:
                    self.api_cache.set('coingecko_contract', {'address': token_address.lower()}, data)
                
                market_data = data.get('market_data', {})
                
                # Extract market cap and volume as liquidity proxy
                market_cap = market_data.get('market_cap', {}).get('usd', 0)
                volume_24h = market_data.get('total_volume', {}).get('usd', 0)
                
                # Use market cap as liquidity estimate (more stable than volume)
                liquidity_usd = market_cap
                
                # Get genesis date for age calculation
                genesis_date = data.get('genesis_date')
                age_days = 0
                
                if genesis_date:
                    try:
                        genesis_dt = datetime.strptime(genesis_date, '%Y-%m-%d')
                        age_days = (datetime.now() - genesis_dt).days
                    except:
                        pass
                
                return {
                    'liquidity_usd': liquidity_usd,
                    'age_days': age_days,
                    'volume_24h': volume_24h
                }
            
            elif response.status_code == 429:
                # Rate limited
                time.sleep(60)
                return {'liquidity_usd': 0, 'age_days': 0, 'volume_24h': 0}
            
            else:
                return {'liquidity_usd': 0, 'age_days': 0, 'volume_24h': 0}
                
        except Exception as e:
            print(f"[DEX Analyzer] CoinGecko error: {e}")
            return {'liquidity_usd': 0, 'age_days': 0, 'volume_24h': 0}
    
    def get_contract_creation_date(self, address: str) -> Optional[int]:
        """Get contract creation date from Etherscan (returns days since creation)"""
        if not self.etherscan_api_key:
            return None
            
        try:
            params = {
                'chainid': '1',
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': 1,
                'sort': 'asc',
                'apikey': self.etherscan_api_key
            }
            
            response = requests.get(self.etherscan_url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1' and data.get('result'):
                # First transaction timestamp
                first_tx = data['result'][0]
                timestamp = int(first_tx.get('timeStamp', 0))
                
                if timestamp > 0:
                    age_seconds = time.time() - timestamp
                    age_days = int(age_seconds / 86400)
                    return age_days
            
            return None
            
        except Exception as e:
            print(f"[DEX Analyzer] Etherscan error: {e}")
            return None
    
    def analyze_token(self, token_address: str) -> Dict[str, float]:
        """
        Complete token analysis
        Returns: liquidity_usd, pair_created_days
        """
        # Check cache
        cache_key = token_address.lower()
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            # Cache valid for 1 hour
            if time.time() - cache_time < 3600:
                return cached_data
        
        # Default values
        result = {
            'total_liquidity_usd': 0.0,
            'pair_created_days': 0,
        }
        
        try:
            # Get market data from CoinGecko
            market_data = self.get_token_market_data(token_address)
            result['total_liquidity_usd'] = market_data['liquidity_usd']
            result['pair_created_days'] = market_data['age_days']
            
            # If CoinGecko doesn't have age, try Etherscan
            if result['pair_created_days'] == 0:
                etherscan_age = self.get_contract_creation_date(token_address)
                if etherscan_age:
                    result['pair_created_days'] = etherscan_age
            
            # Rate limiting
            time.sleep(self.rate_limit_wait)
            
        except Exception as e:
            print(f"[DEX Analyzer] Error: {e}")
        
        # Cache result
        self.cache[cache_key] = (result, time.time())
        return result


# Quick test
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    etherscan_key = os.getenv('ETHERSCAN_API_KEY', '')
    analyzer = DexAnalyzer(etherscan_api_key=etherscan_key)
    
    # Test with WETH (should have high liquidity and old age)
    weth = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    print(f"Testing WETH: {weth}")
    data = analyzer.analyze_token(weth)
    print(f"Liquidity: ${data['total_liquidity_usd']:,.0f}")
    print(f"Age: {data['pair_created_days']} days")
    
    # Test with USDT
    usdt = '0xdAC17F958D2ee523a2206206994597C13D831ec7'
    print(f"\nTesting USDT: {usdt}")
    data = analyzer.analyze_token(usdt)
    print(f"Liquidity: ${data['total_liquidity_usd']:,.0f}")
    print(f"Age: {data['pair_created_days']} days")
    
    # Test with random address (should return 0s)
    random = '0x1234567890123456789012345678901234567890'
    print(f"\nTesting random address: {random}")
    data = analyzer.analyze_token(random)
    print(f"Liquidity: ${data['total_liquidity_usd']:,.0f}")
    print(f"Age: {data['pair_created_days']} days")
