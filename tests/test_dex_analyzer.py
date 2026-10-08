"""Test DEX Analyzer with different endpoints"""
import requests
import json

# Test addresses
weth = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'  # Should have huge liquidity
usdt = '0xdAC17F958D2ee523a2206206994597C13D831ec7'  # Should have huge liquidity

print("Testing Uniswap V2 Subgraph Query\n")

# Try the current endpoint
uniswap_v2_url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"

query = """
{
  pairs(first: 5, where: {token0: "%s"}) {
    id
    reserveUSD
    createdAtTimestamp
  }
}
""" % weth.lower()

print(f"Testing WETH: {weth}")
print(f"Endpoint: {uniswap_v2_url}")
print(f"Query: {query[:100]}...")

try:
    response = requests.post(
        uniswap_v2_url,
        json={'query': query},
        timeout=15
    )
    print(f"\nResponse status: {response.status_code}")
    data = response.json()
    print(f"Response keys: {data.keys()}")
    
    if 'errors' in data:
        print(f"Errors: {data['errors']}")
    
    if 'data' in data:
        pairs = data.get('data', {}).get('pairs', [])
        print(f"Pairs found: {len(pairs)}")
        if pairs:
            for pair in pairs[:3]:
                print(f"  - Pair {pair['id'][:10]}...: ${float(pair['reserveUSD']):,.2f}")
        else:
            print("  No pairs found")
            print(f"Full data response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"No data field in response: {json.dumps(data, indent=2)[:500]}")
        
except Exception as e:
    print(f"Error: {e}")

# Try alternative query format
print("\n\n--- Testing Alternative Query Format ---")
query2 = """
query {
  pairs(first: 5, orderBy: reserveUSD, orderDirection: desc, where: {token0: "%s"}) {
    id
    token0 {
      symbol
    }
    token1 {
      symbol
    }
    reserveUSD
    createdAtTimestamp
  }
}
""" % weth.lower()

try:
    response = requests.post(
        uniswap_v2_url,
        json={'query': query2},
        timeout=15
    )
    data = response.json()
    print(f"Response status: {response.status_code}")
    
    if 'errors' in data:
        print(f"Errors: {data['errors']}")
    
    pairs = data.get('data', {}).get('pairs', [])
    print(f"Pairs found: {len(pairs)}")
    if pairs:
        for pair in pairs[:3]:
            print(f"  - {pair['token0']['symbol']}/{pair['token1']['symbol']}: ${float(pair['reserveUSD']):,.2f}")
            
except Exception as e:
    print(f"Error: {e}")

# Try the decentralized endpoint
print("\n\n--- Testing Decentralized Endpoint ---")
decentralized_url = "https://gateway.thegraph.com/api/[api-key]/subgraphs/id/EYCKATKGBKLWvSfwvBjzfCBmGwYNdVkduYXVivCsLRFu"

print("Note: Decentralized endpoint requires API key")
print("URL format: https://gateway.thegraph.com/api/[api-key]/subgraphs/id/...")
