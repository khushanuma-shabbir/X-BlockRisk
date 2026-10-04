"""
Enterprise-grade rate limiter with Redis backend
Prevents API abuse and manages Etherscan rate limits (5 calls/sec free tier)
"""

import time
import redis
from functools import wraps
from typing import Optional
import hashlib

class RateLimiter:
    """
    Distributed rate limiter using Redis sliding window algorithm
    Supports per-IP, per-user, and per-API-key limits
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        # Fallback to in-memory if Redis unavailable (dev mode)
        self.redis = redis_client
        self.memory_cache = {} if not redis_client else None
        
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check if request is allowed using sliding window algorithm
        
        Returns: (allowed: bool, retry_after: int seconds)
        """
        if self.redis:
            return self._redis_check(key, max_requests, window_seconds)
        else:
            return self._memory_check(key, max_requests, window_seconds)
    
    def _redis_check(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """Redis-based sliding window rate limiting"""
        now = time.time()
        window_key = f"rate_limit:{key}"
        
        # Remove old entries outside window
        self.redis.zremrangebyscore(window_key, 0, now - window_seconds)
        
        # Count requests in current window
        current_requests = self.redis.zcard(window_key)
        
        if current_requests < max_requests:
            # Add current request
            self.redis.zadd(window_key, {str(now): now})
            self.redis.expire(window_key, window_seconds)
            return True, 0
        else:
            # Calculate retry after (oldest request + window)
            oldest = self.redis.zrange(window_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now) + 1
                return False, retry_after
            return False, window_seconds
    
    def _memory_check(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """In-memory fallback for development"""
        now = time.time()
        
        if key not in self.memory_cache:
            self.memory_cache[key] = []
        
        # Remove old entries
        self.memory_cache[key] = [t for t in self.memory_cache[key] if t > now - window_seconds]
        
        if len(self.memory_cache[key]) < max_requests:
            self.memory_cache[key].append(now)
            return True, 0
        else:
            oldest = min(self.memory_cache[key])
            retry_after = int(oldest + window_seconds - now) + 1
            return False, retry_after


class APIRateLimiter:
    """
    Multi-tier rate limiting for external APIs
    - Etherscan: 5 calls/sec (free), 100 calls/sec (paid)
    - Global per-user: 10 addresses/minute
    - Global per-IP: 100 requests/hour
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.limiter = RateLimiter(redis_client)
        
        # Rate limit configurations
        self.ETHERSCAN_FREE_LIMIT = (5, 1)  # 5 calls per second
        self.ETHERSCAN_PAID_LIMIT = (100, 1)  # 100 calls per second
        self.USER_LIMIT = (10, 60)  # 10 addresses per minute
        self.IP_LIMIT = (100, 3600)  # 100 requests per hour
    
    def check_etherscan_limit(self, api_key: str, is_paid: bool = False) -> tuple[bool, int]:
        """Check Etherscan API rate limit"""
        key = f"etherscan:{hashlib.md5(api_key.encode()).hexdigest()}"
        limit = self.ETHERSCAN_PAID_LIMIT if is_paid else self.ETHERSCAN_FREE_LIMIT
        return self.limiter.is_allowed(key, limit[0], limit[1])
    
    def check_user_limit(self, user_id: str) -> tuple[bool, int]:
        """Check per-user analysis limit"""
        key = f"user:{user_id}"
        return self.limiter.is_allowed(key, self.USER_LIMIT[0], self.USER_LIMIT[1])
    
    def check_ip_limit(self, ip_address: str) -> tuple[bool, int]:
        """Check per-IP limit (DDoS protection)"""
        key = f"ip:{ip_address}"
        return self.limiter.is_allowed(key, self.IP_LIMIT[0], self.IP_LIMIT[1])
    
    def check_all(self, user_id: str, ip_address: str, api_key: str) -> tuple[bool, str]:
        """
        Check all rate limits
        Returns: (allowed: bool, error_message: str)
        """
        # Check IP first (fastest to block DDoS)
        allowed, retry = self.check_ip_limit(ip_address)
        if not allowed:
            return False, f"Rate limit exceeded. Try again in {retry} seconds."
        
        # Check user limit
        allowed, retry = self.check_user_limit(user_id)
        if not allowed:
            return False, f"Too many requests. You can analyze {self.USER_LIMIT[0]} addresses per minute. Retry in {retry}s."
        
        # Check Etherscan API limit
        allowed, retry = self.check_etherscan_limit(api_key)
        if not allowed:
            return False, f"API rate limit reached. Retry in {retry} seconds."
        
        return True, ""


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Decorator for rate limiting function calls
    Usage: @rate_limit(max_requests=5, window_seconds=1)
    """
    limiter = RateLimiter()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as key
            key = f"func:{func.__name__}"
            allowed, retry = limiter.is_allowed(key, max_requests, window_seconds)
            
            if not allowed:
                raise RuntimeError(f"Rate limit exceeded. Retry after {retry} seconds.")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global instance (initialize in main app with Redis connection)
global_rate_limiter: Optional[APIRateLimiter] = None

def init_rate_limiter(redis_url: Optional[str] = None):
    """Initialize global rate limiter with Redis connection"""
    global global_rate_limiter
    
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url, decode_responses=False)
            redis_client.ping()  # Test connection
            global_rate_limiter = APIRateLimiter(redis_client)
            print("[SECURITY] Rate limiter initialized with Redis backend")
        except Exception as e:
            print(f"[WARNING] Redis connection failed: {e}. Using in-memory fallback.")
            global_rate_limiter = APIRateLimiter(None)
    else:
        # Development mode - in-memory
        global_rate_limiter = APIRateLimiter(None)
        print("[SECURITY] Rate limiter initialized (in-memory mode)")
