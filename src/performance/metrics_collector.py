"""
Performance metrics collection and monitoring
Tracks API latency, cache hit rates, model inference time
"""

import time
from typing import Dict, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
import statistics

@dataclass
class Metric:
    """Single metric measurement"""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """
    Collects and aggregates performance metrics
    Used for monitoring, alerting, and optimization
    """
    
    def __init__(self, retention_seconds: int = 3600):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.retention_seconds = retention_seconds
    
    def record(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record a single metric"""
        metric = Metric(metric_name, value, tags=tags or {})
        self.metrics[metric_name].append(metric)
    
    def record_duration(self, metric_name: str, start_time: float, tags: Dict[str, str] = None):
        """Record duration from start time to now"""
        duration = time.time() - start_time
        self.record(metric_name, duration, tags)
    
    def get_stats(self, metric_name: str, last_seconds: int = 300) -> Dict[str, float]:
        """
        Get statistics for a metric over time window
        Returns: min, max, mean, median, p95, p99
        """
        cutoff = time.time() - last_seconds
        recent = [m.value for m in self.metrics[metric_name] if m.timestamp >= cutoff]
        
        if not recent:
            return {}
        
        sorted_values = sorted(recent)
        return {
            'count': len(recent),
            'min': min(recent),
            'max': max(recent),
            'mean': statistics.mean(recent),
            'median': statistics.median(recent),
            'p95': sorted_values[int(len(sorted_values) * 0.95)] if len(sorted_values) > 20 else max(recent),
            'p99': sorted_values[int(len(sorted_values) * 0.99)] if len(sorted_values) > 100 else max(recent),
        }
    
    def get_rate(self, metric_name: str, last_seconds: int = 60) -> float:
        """Get event rate (events per second)"""
        cutoff = time.time() - last_seconds
        count = len([m for m in self.metrics[metric_name] if m.timestamp >= cutoff])
        return count / last_seconds
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Get current stats for all metrics"""
        return {
            name: self.get_stats(name, last_seconds=300)
            for name in self.metrics.keys()
        }
    
    def clear_old_metrics(self):
        """Clean up old metrics (called periodically)"""
        cutoff = time.time() - self.retention_seconds
        for metric_name in list(self.metrics.keys()):
            queue = self.metrics[metric_name]
            while queue and queue[0].timestamp < cutoff:
                queue.popleft()


# Context manager for timing operations
class Timer:
    """
    Context manager for measuring operation duration
    Usage:
        with Timer("api_call", metrics_collector):
            fetch_data()
    """
    
    def __init__(self, metric_name: str, collector: MetricsCollector, tags: Dict = None):
        self.metric_name = metric_name
        self.collector = collector
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Add error tag if exception occurred
        if exc_type:
            self.tags['error'] = exc_type.__name__
        
        self.collector.record(self.metric_name, duration, self.tags)


# Standard metrics tracked
class MetricNames:
    """Standard metric names for consistency"""
    
    # API performance
    API_ETHERSCAN_LATENCY = "api.etherscan.latency"
    API_ETHERSCAN_ERRORS = "api.etherscan.errors"
    
    # Cache performance
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_HIT_RATE = "cache.hit_rate"
    
    # Model performance
    MODEL_INFERENCE_TIME = "model.inference.time"
    MODEL_PREDICTIONS = "model.predictions"
    
    # Feature engineering
    FEATURE_COMPUTATION_TIME = "features.computation.time"
    
    # Overall
    ANALYSIS_TOTAL_TIME = "analysis.total.time"
    ANALYSIS_SUCCESS = "analysis.success"
    ANALYSIS_FAILURE = "analysis.failure"
    
    # Rate limiting
    RATE_LIMIT_HITS = "ratelimit.hits"
    RATE_LIMIT_BLOCKS = "ratelimit.blocks"


# Global instance
global_metrics: Optional[MetricsCollector] = None

def init_metrics_collector():
    """Initialize global metrics collector"""
    global global_metrics
    global_metrics = MetricsCollector(retention_seconds=3600)
    print("[PERFORMANCE] Metrics collector initialized")
