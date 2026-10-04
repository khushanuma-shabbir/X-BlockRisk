"""
Real-time progress tracking with websocket support
Shows users exactly what's happening during analysis
"""

from typing import Dict, Callable, Optional
import time

class ProgressTracker:
    """
    Track and report progress for long-running operations
    Integrates with async jobs and Streamlit UI
    """
    
    def __init__(self, job_id: str, callback: Optional[Callable] = None):
        self.job_id = job_id
        self.callback = callback  # For real-time updates (websocket, etc.)
        self.stages = []
        self.current_stage = 0
        self.start_time = time.time()
    
    def define_stages(self, stages: list[tuple[str, int]]):
        """
        Define analysis stages with weights
        Example: [("Validation", 5), ("Fetch data", 50), ("Model inference", 40), ("Generate report", 5)]
        """
        self.stages = stages
    
    def update(self, stage_name: str, progress: float, message: str = ""):
        """
        Update progress for current stage
        progress: 0.0 to 1.0 (percentage of stage complete)
        """
        # Find stage
        for i, (name, weight) in enumerate(self.stages):
            if name == stage_name:
                self.current_stage = i
                break
        
        # Calculate overall progress
        completed_weight = sum(w for _, w in self.stages[:self.current_stage])
        current_stage_weight = self.stages[self.current_stage][1]
        total_weight = sum(w for _, w in self.stages)
        
        overall_progress = (completed_weight + current_stage_weight * progress) / total_weight
        
        # Format message
        elapsed = time.time() - self.start_time
        eta = elapsed / overall_progress - elapsed if overall_progress > 0 else 0
        
        progress_info = {
            'job_id': self.job_id,
            'stage': stage_name,
            'stage_progress': int(progress * 100),
            'overall_progress': int(overall_progress * 100),
            'message': message,
            'elapsed_seconds': round(elapsed, 1),
            'eta_seconds': round(eta, 1),
            'timestamp': time.time()
        }
        
        # Callback for real-time updates
        if self.callback:
            self.callback(progress_info)
        
        return progress_info
    
    def complete(self, message: str = "Complete"):
        """Mark job as complete"""
        return self.update(self.stages[-1][0], 1.0, message)


class AnalysisProgressStages:
    """
    Standard progress stages for address analysis
    Provides consistent UX across the application
    """
    
    STAGES = [
        ("Input Validation", 5),
        ("Rate Limit Check", 5),
        ("Cache Lookup", 10),
        ("Fetch Transactions", 40),
        ("Feature Engineering", 15),
        ("Model Inference", 20),
        ("Generate Explanation", 5)
    ]
    
    @staticmethod
    def create_tracker(job_id: str, callback: Optional[Callable] = None) -> ProgressTracker:
        """Create pre-configured tracker for address analysis"""
        tracker = ProgressTracker(job_id, callback)
        tracker.define_stages(AnalysisProgressStages.STAGES)
        return tracker
