"""
Enterprise Security Layer for Blockchain Fraud Detection
Implements: Rate limiting, caching, key rotation, input validation
"""

from .rate_limiter import init_rate_limiter, global_rate_limiter
from .cache_manager import init_cache, global_cache, global_address_cache
from .key_manager import init_key_manager, global_key_manager
from .input_validator import InputValidator, SecurityValidator

__all__ = [
    'init_rate_limiter',
    'init_cache',
    'init_key_manager',
    'global_rate_limiter',
    'global_cache',
    'global_address_cache',
    'global_key_manager',
    'InputValidator',
    'SecurityValidator'
]

def initialize_security_layer(redis_url: str = None):
    """
    Initialize all security components in correct order
    Call this at application startup
    """
    print("[SECURITY] Initializing enterprise security layer...")
    
    # 1. Key management (load API keys)
    init_key_manager()
    
    # 2. Caching (Redis + memory)
    init_cache(redis_url=redis_url, max_memory=1000)
    
    # 3. Rate limiting (Redis + memory)
    init_rate_limiter(redis_url=redis_url)
    
    print("[SECURITY] ✓ Security layer initialized successfully")
