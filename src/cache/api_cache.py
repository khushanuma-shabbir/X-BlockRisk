"""
API Response Cache - Enables Offline Reproduction
Saves API responses to disk for reproducibility
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib

class APICache:
    """Cache API responses to enable offline reproduction"""
    
    def __init__(self, cache_dir: str = "cache/api_responses"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = True
        self.ttl = 86400 * 7  # 7 days default TTL
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and params"""
        # Sort params for consistent hashing
        param_str = json.dumps(params, sort_keys=True)
        key_str = f"{endpoint}:{param_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            
            # Check expiration
            if time.time() - cached['timestamp'] > self.ttl:
                return None
            
            return cached['response']
        except:
            return None
    
    def set(self, endpoint: str, params: Dict[str, Any], response: Dict[str, Any]) -> None:
        """Save response to cache"""
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(endpoint, params)
        cache_path = self._get_cache_path(cache_key)
        
        cached_data = {
            'endpoint': endpoint,
            'params': params,
            'response': response,
            'timestamp': time.time()
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            print(f"[Cache] Warning: Could not save cache: {e}")
    
    def clear(self) -> int:
        """Clear all cache files"""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'total_files': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }


# Global cache instance
_global_cache = None

def get_cache() -> APICache:
    """Get global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = APICache()
    return _global_cache


# Quick test
if __name__ == '__main__':
    cache = APICache("test_cache")
    
    # Test set and get
    endpoint = "etherscan/getabi"
    params = {'address': '0xtest123', 'apikey': 'hidden'}
    response = {'status': '1', 'result': 'test_abi_data'}
    
    print("Testing API Cache...")
    
    # Set
    cache.set(endpoint, params, response)
    print(f"✓ Cached response for {endpoint}")
    
    # Get
    cached = cache.get(endpoint, params)
    assert cached == response, "Cache get failed"
    print(f"✓ Retrieved cached response")
    
    # Stats
    stats = cache.get_stats()
    print(f"✓ Cache stats: {stats['total_files']} files, {stats['total_size_mb']:.2f} MB")
    
    # Clear
    count = cache.clear()
    print(f"✓ Cleared {count} cache files")
    
    print("\nAPI Cache working correctly!")
