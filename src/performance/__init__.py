"""
Performance optimization layer for blockchain fraud detection
Implements: Async processing, background jobs, progress tracking, metrics
"""

from .async_processor import (
    init_async_processor,
    global_async_analyzer,
    global_batch_processor,
    AsyncAnalyzer,
    BatchProcessor,
    AnalysisJob,
    JobStatus
)

from .progress_tracker import (
    ProgressTracker,
    AnalysisProgressStages
)

from .metrics_collector import (
    init_metrics_collector,
    global_metrics,
    MetricsCollector,
    Timer,
    MetricNames
)

__all__ = [
    'init_async_processor',
    'init_metrics_collector',
    'global_async_analyzer',
    'global_batch_processor',
    'global_metrics',
    'AsyncAnalyzer',
    'BatchProcessor',
    'AnalysisJob',
    'JobStatus',
    'ProgressTracker',
    'AnalysisProgressStages',
    'MetricsCollector',
    'Timer',
    'MetricNames'
]

def initialize_performance_layer(max_workers: int = 10):
    """
    Initialize all performance components
    Call this at application startup
    """
    print("[PERFORMANCE] Initializing performance optimization layer...")
    
    # 1. Async processor (background jobs)
    init_async_processor(max_workers=max_workers)
    
    # 2. Metrics collector (monitoring)
    init_metrics_collector()
    
    print("[PERFORMANCE] ✓ Performance layer initialized successfully")
