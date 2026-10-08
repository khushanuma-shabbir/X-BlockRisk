"""Test CoinGecko API for token liquidity data"""
import requests
import time

# CoinGecko has token info including market cap, volume, liquidity
coingecko_url = "https://api.coingecko.com/api/v3"

# Test with known tokens
test_tokens = {
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
}

print("Testing CoinGecko API for Liquidity Data\n")

for name, address in test_tokens.items():
    print(f"\n--- {name} ({address}) ---")
    
    try:
        # Search for token by contract address
        url = f"{coingecko_url}/coins/ethereum/contract/{address}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract market data
            market_data = data.get('market_data', {})
            market_cap = market_data.get('market_cap', {}).get('usd', 0)
            total_volume = market_data.get('total_volume', {}).get('usd', 0)
            
            # Extract liquidity if available
            liquidity = market_data.get('total_value_locked', {})
            
            print(f"  Market Cap: ${market_cap:,.0f}")
            print(f"  24h Volume: ${total_volume:,.0f}")
            
            # Genesis date as proxy for age
            genesis_date = data.get('genesis_date')
            if genesis_date:
                print(f"  Genesis Date: {genesis_date}")
            
            # Contract creation (approximate age)
            contract_info = data.get('detail_platforms', {}).get('ethereum', {})
            contract_created = contract_info.get('contract_address')
            print(f"  Contract Verified: {'Yes' if contract_created else 'Unknown'}")
            
        elif response.status_code == 429:
            print("  Rate limited - waiting...")
            time.sleep(60)
        else:
            print(f"  Error {response.status_code}: {response.text[:100]}")
            
    except Exception as e:
        print(f"  Exception: {e}")
    
    time.sleep(2)  # Rate limiting

print("\n\n--- Testing Free Tier Limits ---")
print("CoinGecko Free tier: 10-50 calls/min")
print("For production: Need to handle rate limiting or use paid tier")
