"""
Etherscan API Integration for Smart Contract Analysis
Fetches contract source code and metadata from Etherscan.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')
ETHERSCAN_API_URL = 'https://api.etherscan.io/api'


def fetch_contract_source(contract_address):
    """
    Fetch verified contract source code from Etherscan
    
    Args:
        contract_address: Ethereum contract address (0x...)
    
    Returns:
        dict with:
        - verified: bool
        - source_code: str (if verified)
        - contract_name: str
        - compiler_version: str
        - optimization: bool
        - error: str (if any error occurred)
    """
    if not ETHERSCAN_API_KEY:
        return {
            'verified': False,
            'error': 'No Etherscan API key configured'
        }
    
    # Clean address
    contract_address = contract_address.strip()
    if not contract_address.startswith('0x'):
        return {
            'verified': False,
            'error': 'Invalid address format (must start with 0x)'
        }
    
    print(f"\n[INFO] Fetching contract source from Etherscan...")
    print(f"[INFO] Contract: {contract_address}")
    
    try:
        # Get contract source code
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': contract_address,
            'apikey': ETHERSCAN_API_KEY
        }
        
        response = requests.get(ETHERSCAN_API_URL, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') != '1':
            return {
                'verified': False,
                'error': f"Etherscan API error: {data.get('message', 'Unknown error')}"
            }
        
        result = data.get('result', [{}])[0]
        
        # Check if verified
        source_code = result.get('SourceCode', '')
        if not source_code or source_code == '':
            print(f"[WARNING] Contract not verified on Etherscan")
            return {
                'verified': False,
                'contract_name': 'Unknown',
                'error': None
            }
        
        print(f"[INFO] Contract verified: {result.get('ContractName', 'Unknown')}")
        print(f"[INFO] Source code length: {len(source_code)} characters")
        
        return {
            'verified': True,
            'source_code': source_code,
            'contract_name': result.get('ContractName', 'Unknown'),
            'compiler_version': result.get('CompilerVersion', ''),
            'optimization': result.get('OptimizationUsed') == '1',
            'runs': result.get('Runs', ''),
            'constructor_arguments': result.get('ConstructorArguments', ''),
            'abi': result.get('ABI', ''),
            'error': None
        }
    
    except requests.exceptions.Timeout:
        return {
            'verified': False,
            'error': 'Etherscan API timeout'
        }
    except Exception as e:
        return {
            'verified': False,
            'error': f'Error fetching contract: {str(e)}'
        }


def fetch_contract_metadata(contract_address):
    """
    Fetch additional contract metadata
    
    Returns:
        dict with transaction count, balance, etc.
    """
    if not ETHERSCAN_API_KEY:
        return {}
    
    try:
        # Get transaction count
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionCount',
            'address': contract_address,
            'tag': 'latest',
            'apikey': ETHERSCAN_API_KEY
        }
        
        response = requests.get(ETHERSCAN_API_URL, params=params, timeout=10)
        data = response.json()
        
        tx_count = 0
        if data.get('result'):
            tx_count = int(data['result'], 16)  # Convert hex to int
        
        return {
            'transaction_count': tx_count
        }
    
    except Exception as e:
        print(f"[WARNING] Could not fetch metadata: {e}")
        return {}
