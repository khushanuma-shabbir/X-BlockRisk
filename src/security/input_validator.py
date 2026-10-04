"""
Enterprise-grade input validation and sanitization
Prevents injection attacks, API abuse, and invalid requests
"""

import re
from typing import Optional, Tuple
from eth_utils import is_address, to_checksum_address
import base58

class InputValidator:
    """
    Validates and sanitizes blockchain addresses and transaction hashes
    Supports: Ethereum, Solana, BSC, Polygon
    """
    
    # Regex patterns
    ETH_ADDRESS_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')
    ETH_TX_PATTERN = re.compile(r'^0x[a-fA-F0-9]{64}$')
    SOLANA_ADDRESS_PATTERN = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
    
    # Blacklisted patterns (known attack vectors)
    BLACKLIST_PATTERNS = [
        r'<script', r'javascript:', r'onerror=', r'onclick=',  # XSS
        r'union.*select', r'drop.*table', r'insert.*into',     # SQL injection
        r'\.\./\.\.',  # Path traversal
    ]
    
    @staticmethod
    def validate_ethereum_address(address: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate Ethereum address (EIP-55 checksum aware)
        
        Returns: (valid: bool, normalized_address: str, error: str)
        """
        if not address:
            return False, None, "Address cannot be empty"
        
        # Remove whitespace
        address = address.strip()
        
        # Check length and format
        if not InputValidator.ETH_ADDRESS_PATTERN.match(address):
            return False, None, "Invalid Ethereum address format. Must be 0x followed by 40 hex characters."
        
        # Check for blacklisted patterns
        for pattern in InputValidator.BLACKLIST_PATTERNS:
            if re.search(pattern, address.lower()):
                return False, None, "Suspicious input detected"
        
        # Validate checksum if mixed case (EIP-55)
        try:
            if address != address.lower() and address != address.upper():
                # Has mixed case, validate checksum
                if not is_address(address):
                    return False, None, "Invalid EIP-55 checksum"
            
            # Normalize to checksum format
            normalized = to_checksum_address(address)
            return True, normalized, None
        except Exception as e:
            return False, None, f"Address validation failed: {str(e)}"
    
    @staticmethod
    def validate_ethereum_tx(tx_hash: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate Ethereum transaction hash
        
        Returns: (valid: bool, normalized_hash: str, error: str)
        """
        if not tx_hash:
            return False, None, "Transaction hash cannot be empty"
        
        tx_hash = tx_hash.strip()
        
        if not InputValidator.ETH_TX_PATTERN.match(tx_hash):
            return False, None, "Invalid transaction hash format. Must be 0x followed by 64 hex characters."
        
        return True, tx_hash.lower(), None
    
    @staticmethod
    def validate_solana_address(address: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate Solana address (base58 format)
        
        Returns: (valid: bool, normalized_address: str, error: str)
        """
        if not address:
            return False, None, "Address cannot be empty"
        
        address = address.strip()
        
        # Check format
        if not InputValidator.SOLANA_ADDRESS_PATTERN.match(address):
            return False, None, "Invalid Solana address format"
        
        # Validate base58 encoding
        try:
            decoded = base58.b58decode(address)
            if len(decoded) != 32:
                return False, None, "Invalid Solana address length"
            return True, address, None
        except Exception:
            return False, None, "Invalid base58 encoding"
    
    @staticmethod
    def detect_blockchain(input_str: str) -> Optional[str]:
        """
        Auto-detect blockchain type from address format
        
        Returns: 'ethereum', 'solana', or None
        """
        input_str = input_str.strip()
        
        if input_str.startswith('0x'):
            if len(input_str) == 42:
                return 'ethereum'
            elif len(input_str) == 66:
                return 'ethereum_tx'
        elif InputValidator.SOLANA_ADDRESS_PATTERN.match(input_str):
            return 'solana'
        
        return None
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 100) -> str:
        """
        Sanitize user input (remove dangerous characters)
        """
        if not input_str:
            return ""
        
        # Truncate
        input_str = input_str[:max_length]
        
        # Remove control characters
        input_str = ''.join(char for char in input_str if char.isprintable())
        
        # Remove dangerous patterns
        for pattern in InputValidator.BLACKLIST_PATTERNS:
            input_str = re.sub(pattern, '', input_str, flags=re.IGNORECASE)
        
        return input_str.strip()
    
    @staticmethod
    def validate_transaction_limit(tx_count: int, max_allowed: int = 100000) -> Tuple[bool, Optional[str]]:
        """
        Check if wallet has too many transactions (timeout risk)
        
        Returns: (acceptable: bool, warning: str)
        """
        if tx_count > max_allowed:
            return False, f"Address has {tx_count:,} transactions (max {max_allowed:,}). Analysis may timeout."
        elif tx_count > 50000:
            return True, f"Address has {tx_count:,} transactions. Analysis may take 30-60 seconds."
        
        return True, None


class SecurityValidator:
    """
    Additional security checks for production deployment
    """
    
    @staticmethod
    def check_honeypot_indicators(address: str, features: dict) -> list[str]:
        """
        Detect honeypot patterns in wallet behavior
        Returns list of red flags
        """
        flags = []
        
        # Only receives, never sends (potential honeypot)
        if features.get('Received Tnx', 0) > 10 and features.get('Sent tnx', 0) == 0:
            flags.append("⚠️ Honeypot warning: Wallet only receives funds (never sends)")
        
        # Massive inflow, minimal outflow
        received = features.get('total ether received', 0)
        sent = features.get('total Ether sent', 0)
        if received > 100 and sent < received * 0.01:
            flags.append("⚠️ Suspicious: Received >100 ETH but sent <1%")
        
        # Single sender dominance
        unique_from = features.get('Unique Received From Addresses', 0)
        total_received = features.get('Received Tnx', 0)
        if total_received > 20 and unique_from < 3:
            flags.append("⚠️ Warning: Receives from very few addresses (possible wash trading)")
        
        return flags
    
    @staticmethod
    def check_smart_contract(address: str) -> Tuple[bool, Optional[str]]:
        """
        Check if address is a smart contract (requires different analysis)
        """
        # TODO: Call Etherscan API to check if contract
        # For now, just a placeholder
        return False, None
