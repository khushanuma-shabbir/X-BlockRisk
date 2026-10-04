"""
Dashboard Metrics Module
Aggregates system performance and detection statistics for admin dashboard.

Production Features:
- Real-time system health monitoring
- Detection statistics (total scans, risk distribution)
- Performance metrics (response time, cache hit rate)
- User activity tracking
- Historical trend analysis
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardMetrics:
    """
    Aggregates and provides dashboard metrics
    """
    
    def __init__(self, storage_path: str = 'data/metrics'):
        """
        Initialize dashboard metrics
        
        Args:
            storage_path: Directory to store metrics data
        """
        self.storage_path = storage_path
        self.metrics_file = os.path.join(storage_path, 'dashboard_metrics.json')
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing metrics
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict:
        """Load metrics from storage"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading metrics: {e}")
        
        # Initialize empty metrics
        return {
            'system': {
                'uptime_start': datetime.now().isoformat(),
                'total_requests': 0,
                'total_errors': 0,
                'last_updated': datetime.now().isoformat()
            },
            'detection': {
                'total_scans': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'average_risk_score': 0,
                'scans_by_chain': {},
                'last_24h_scans': []
            },
            'performance': {
                'avg_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'cache_hit_rate': 0,
                'api_calls_saved': 0,
                'response_times': []
            },
            'users': {
                'total_users': 0,
                'active_sessions': 0,
                'searches_by_user': {}
            }
        }
    
    def _save_metrics(self):
        """Save metrics to storage"""
        try:
            self.metrics['system']['last_updated'] = datetime.now().isoformat()
            
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return False
    
    # ===== TRACKING METHODS =====
    
    def record_scan(
        self,
        risk_score: float,
        risk_category: str,
        response_time: float,
        chain: str = 'ethereum',
        cache_hit: bool = False,
        user_id: Optional[str] = None
    ):
        """
        Record a completed scan
        
        Args:
            risk_score: Risk score (0-100)
            risk_category: Risk category
            response_time: Response time in seconds
            chain: Blockchain network
            cache_hit: Whether result was cached
            user_id: Optional user identifier
        """
        # Update detection metrics
        self.metrics['detection']['total_scans'] += 1
        
        if risk_category == 'High Risk':
            self.metrics['detection']['high_risk_count'] += 1
        elif risk_category == 'Medium Risk':
            self.metrics['detection']['medium_risk_count'] += 1
        else:
            self.metrics['detection']['low_risk_count'] += 1
        
        # Update average risk score
        total = self.metrics['detection']['total_scans']
        current_avg = self.metrics['detection']['average_risk_score']
        new_avg = ((current_avg * (total - 1)) + risk_score) / total
        self.metrics['detection']['average_risk_score'] = round(new_avg, 2)
        
        # Track by chain
        chain_key = chain.lower()
        if chain_key not in self.metrics['detection']['scans_by_chain']:
            self.metrics['detection']['scans_by_chain'][chain_key] = 0
        self.metrics['detection']['scans_by_chain'][chain_key] += 1
        
        # Track last 24h (keep only timestamps)
        now = datetime.now()
        self.metrics['detection']['last_24h_scans'].append(now.isoformat())
        
        # Clean old entries (older than 24h)
        cutoff = now - timedelta(hours=24)
        self.metrics['detection']['last_24h_scans'] = [
            ts for ts in self.metrics['detection']['last_24h_scans']
            if datetime.fromisoformat(ts) > cutoff
        ]
        
        # Update performance metrics
        self.metrics['performance']['response_times'].append(response_time)
        
        # Keep only last 1000 response times
        if len(self.metrics['performance']['response_times']) > 1000:
            self.metrics['performance']['response_times'] = \
                self.metrics['performance']['response_times'][-1000:]
        
        # Recalculate performance stats
        response_times = self.metrics['performance']['response_times']
        if response_times:
            self.metrics['performance']['avg_response_time'] = \
                round(sum(response_times) / len(response_times), 2)
            
            sorted_times = sorted(response_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            
            self.metrics['performance']['p95_response_time'] = \
                round(sorted_times[p95_idx], 2)
            self.metrics['performance']['p99_response_time'] = \
                round(sorted_times[p99_idx], 2)
        
        # Update cache metrics
        if cache_hit:
            self.metrics['performance']['api_calls_saved'] += 1
        
        total_with_cache = self.metrics['detection']['total_scans']
        if total_with_cache > 0:
            self.metrics['performance']['cache_hit_rate'] = round(
                100 * self.metrics['performance']['api_calls_saved'] / total_with_cache,
                1
            )
        
        # Track user activity
        if user_id:
            if user_id not in self.metrics['users']['searches_by_user']:
                self.metrics['users']['searches_by_user'][user_id] = 0
                self.metrics['users']['total_users'] += 1
            
            self.metrics['users']['searches_by_user'][user_id] += 1
        
        # Save to disk
        self._save_metrics()
    
    def record_error(self, error_type: str, error_message: str):
        """
        Record a system error
        
        Args:
            error_type: Type of error
            error_message: Error description
        """
        self.metrics['system']['total_errors'] += 1
        self._save_metrics()
        
        logger.error(f"Error recorded: {error_type} - {error_message}")
    
    # ===== QUERY METHODS =====
    
    def get_system_health(self) -> Dict:
        """
        Get overall system health metrics
        
        Returns:
            dict with system health data
        """
        uptime_start = datetime.fromisoformat(self.metrics['system']['uptime_start'])
        uptime_seconds = (datetime.now() - uptime_start).total_seconds()
        
        total_requests = self.metrics['system']['total_requests']
        total_errors = self.metrics['system']['total_errors']
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Determine health status
        if error_rate < 1 and self.metrics['performance']['avg_response_time'] < 3:
            status = 'healthy'
            status_color = 'green'
        elif error_rate < 5 and self.metrics['performance']['avg_response_time'] < 5:
            status = 'degraded'
            status_color = 'yellow'
        else:
            status = 'unhealthy'
            status_color = 'red'
        
        return {
            'status': status,
            'status_color': status_color,
            'uptime_seconds': int(uptime_seconds),
            'uptime_formatted': self._format_uptime(uptime_seconds),
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': round(error_rate, 2),
            'last_updated': self.metrics['system']['last_updated']
        }
    
    def get_detection_stats(self) -> Dict:
        """
        Get detection statistics
        
        Returns:
            dict with detection metrics
        """
        detection = self.metrics['detection']
        total = detection['total_scans']
        
        return {
            'total_scans': total,
            'high_risk_count': detection['high_risk_count'],
            'high_risk_pct': round(detection['high_risk_count'] / total * 100, 1) if total > 0 else 0,
            'medium_risk_count': detection['medium_risk_count'],
            'medium_risk_pct': round(detection['medium_risk_count'] / total * 100, 1) if total > 0 else 0,
            'low_risk_count': detection['low_risk_count'],
            'low_risk_pct': round(detection['low_risk_count'] / total * 100, 1) if total > 0 else 0,
            'average_risk_score': detection['average_risk_score'],
            'scans_by_chain': detection['scans_by_chain'],
            'scans_last_24h': len(detection['last_24h_scans'])
        }
    
    def get_performance_stats(self) -> Dict:
        """
        Get performance statistics
        
        Returns:
            dict with performance metrics
        """
        perf = self.metrics['performance']
        
        return {
            'avg_response_time': perf['avg_response_time'],
            'p95_response_time': perf['p95_response_time'],
            'p99_response_time': perf['p99_response_time'],
            'cache_hit_rate': perf['cache_hit_rate'],
            'api_calls_saved': perf['api_calls_saved'],
            'total_response_times': len(perf['response_times'])
        }
    
    def get_user_stats(self) -> Dict:
        """
        Get user activity statistics
        
        Returns:
            dict with user metrics
        """
        users = self.metrics['users']
        
        # Find top users
        top_users = sorted(
            users['searches_by_user'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_users': users['total_users'],
            'active_sessions': users['active_sessions'],
            'top_users': [
                {'user_id': uid, 'search_count': count}
                for uid, count in top_users
            ]
        }
    
    def get_hourly_trend(self, hours: int = 24) -> List[Dict]:
        """
        Get scan volume trend by hour
        
        Args:
            hours: Number of hours to include
        
        Returns:
            list of hourly scan counts
        """
        scans = self.metrics['detection']['last_24h_scans']
        
        # Group by hour
        hourly_counts = defaultdict(int)
        
        for scan_time in scans:
            dt = datetime.fromisoformat(scan_time)
            hour_key = dt.strftime('%Y-%m-%d %H:00')
            hourly_counts[hour_key] += 1
        
        # Create full timeline
        now = datetime.now()
        trend = []
        
        for i in range(hours):
            hour_dt = now - timedelta(hours=hours - i - 1)
            hour_key = hour_dt.strftime('%Y-%m-%d %H:00')
            
            trend.append({
                'hour': hour_dt.strftime('%H:00'),
                'count': hourly_counts.get(hour_key, 0)
            })
        
        return trend
    
    def get_full_dashboard(self) -> Dict:
        """
        Get all dashboard metrics in one call
        
        Returns:
            dict with all metrics
        """
        return {
            'system_health': self.get_system_health(),
            'detection_stats': self.get_detection_stats(),
            'performance_stats': self.get_performance_stats(),
            'user_stats': self.get_user_stats(),
            'hourly_trend': self.get_hourly_trend()
        }
    
    # ===== HELPER METHODS =====
    
    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Format uptime as human-readable string"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or len(parts) == 0:
            parts.append(f"{minutes}m")
        
        return " ".join(parts)


# Example usage
if __name__ == '__main__':
    print("Dashboard Metrics Module")
    print("="*60)
    
    metrics = DashboardMetrics()
    
    # Simulate some scans
    for i in range(10):
        metrics.record_scan(
            risk_score=50 + i * 5,
            risk_category='Medium Risk',
            response_time=1.5 + i * 0.1,
            chain='ethereum',
            cache_hit=(i % 3 == 0)
        )
    
    # Get dashboard
    dashboard = metrics.get_full_dashboard()
    
    print("\n✓ Dashboard Metrics Ready")
    print(f"\nSample Metrics:")
    print(f"  Total Scans: {dashboard['detection_stats']['total_scans']}")
    print(f"  Avg Response Time: {dashboard['performance_stats']['avg_response_time']}s")
    print(f"  Cache Hit Rate: {dashboard['performance_stats']['cache_hit_rate']}%")
