"""
API Key rotation and management system
Prevents key exhaustion and enables multi-key load balancing
"""

import os
import time
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

class KeyStatus(Enum):
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    EXHAUSTED = "exhausted"
    INVALID = "invalid"

@dataclass
class APIKey:
    """API Key metadata"""
    key: str
    provider: str  # 'etherscan', 'alchemy', 'infura'
    tier: str  # 'free', 'paid'
    calls_per_second: int
    daily_limit: int
    status: KeyStatus = KeyStatus.ACTIVE
    last_used: float = 0
    daily_usage: int = 0
    last_reset: float = 0

class KeyManager:
    """
    Manages multiple API keys with automatic rotation
    Features:
    - Round-robin load balancing
    - Automatic rate limit detection
    - Fallback to backup keys
    - Daily quota tracking
    """
    
    def __init__(self):
        self.keys: Dict[str, List[APIKey]] = {
            'etherscan': [],
            'alchemy': [],
            'infura': [],
        }
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from environment variables"""
        # Etherscan keys
        etherscan_keys = os.getenv('ETHERSCAN_API_KEYS', '').split(',')
        for i, key in enumerate(etherscan_keys):
            key = key.strip()
            if key:
                tier = 'paid' if i == 0 else 'free'  # First key = paid tier
                self.keys['etherscan'].append(APIKey(
                    key=key,
                    provider='etherscan',
                    tier=tier,
                    calls_per_second=100 if tier == 'paid' else 5,
                    daily_limit=100000 if tier == 'paid' else 100000,
                ))
        
        # Alchemy keys (backup)
        alchemy_key = os.getenv('ALCHEMY_API_KEY', '').strip()
        if alchemy_key:
            self.keys['alchemy'].append(APIKey(
                key=alchemy_key,
                provider='alchemy',
                tier='free',
                calls_per_second=25,
                daily_limit=300000,
            ))
        
        # Infura keys (backup)
        infura_key = os.getenv('INFURA_API_KEY', '').strip()
        if infura_key:
            self.keys['infura'].append(APIKey(
                key=infura_key,
                provider='infura',
                tier='free',
                calls_per_second=10,
                daily_limit=100000,
            ))
    
    def get_key(self, provider: str = 'etherscan') -> Optional[APIKey]:
        """
        Get next available API key (round-robin with health check)
        Returns None if all keys exhausted
        """
        keys = self.keys.get(provider, [])
        if not keys:
            return None
        
        # Reset daily counters if needed
        now = time.time()
        for key in keys:
            if now - key.last_reset > 86400:  # 24 hours
                key.daily_usage = 0
                key.last_reset = now
                if key.status == KeyStatus.EXHAUSTED:
                    key.status = KeyStatus.ACTIVE
        
        # Find active key with lowest usage
        active_keys = [k for k in keys if k.status == KeyStatus.ACTIVE]
        if not active_keys:
            # All keys rate limited, try fallback providers
            return self._get_fallback_key()
        
        # Return key with lowest daily usage
        key = min(active_keys, key=lambda k: k.daily_usage)
        key.last_used = now
        key.daily_usage += 1
        
        # Check if approaching daily limit
        if key.daily_usage >= key.daily_limit * 0.95:
            key.status = KeyStatus.EXHAUSTED
        
        return key
    
    def _get_fallback_key(self) -> Optional[APIKey]:
        """Try backup providers if primary exhausted"""
        for provider in ['alchemy', 'infura']:
            key = self.get_key(provider)
            if key:
                print(f"[KEY MANAGER] Falling back to {provider}")
                return key
        return None
    
    def mark_rate_limited(self, key: APIKey, cooldown_seconds: int = 60):
        """Mark key as rate limited (temporary)"""
        key.status = KeyStatus.RATE_LIMITED
        # TODO: Schedule re-activation after cooldown
    
    def mark_invalid(self, key: APIKey):
        """Mark key as invalid (permanent)"""
        key.status = KeyStatus.INVALID
    
    def get_stats(self) -> Dict:
        """Get key usage statistics"""
        stats = {}
        for provider, keys in self.keys.items():
            stats[provider] = {
                'total_keys': len(keys),
                'active': len([k for k in keys if k.status == KeyStatus.ACTIVE]),
                'rate_limited': len([k for k in keys if k.status == KeyStatus.RATE_LIMITED]),
                'exhausted': len([k for k in keys if k.status == KeyStatus.EXHAUSTED]),
                'total_usage': sum(k.daily_usage for k in keys),
            }
        return stats
    
    def add_key(self, provider: str, key: str, tier: str = 'free'):
        """Dynamically add new API key"""
        limits = {
            'etherscan': {'free': (5, 100000), 'paid': (100, 100000)},
            'alchemy': {'free': (25, 300000), 'paid': (100, 1000000)},
            'infura': {'free': (10, 100000), 'paid': (50, 500000)},
        }
        
        calls_per_sec, daily_limit = limits.get(provider, {}).get(tier, (5, 100000))
        
        self.keys[provider].append(APIKey(
            key=key,
            provider=provider,
            tier=tier,
            calls_per_second=calls_per_sec,
            daily_limit=daily_limit,
        ))


# Global instance
global_key_manager: Optional[KeyManager] = None

def init_key_manager():
    """Initialize global key manager"""
    global global_key_manager
    global_key_manager = KeyManager()
    
    stats = global_key_manager.get_stats()
    total_keys = sum(s['total_keys'] for s in stats.values())
    print(f"[KEY MANAGER] Initialized with {total_keys} API keys")
    
    if total_keys == 0:
        print("[WARNING] No API keys configured! Add ETHERSCAN_API_KEYS to .env")
