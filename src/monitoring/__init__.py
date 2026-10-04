"""
Monitoring Layer Module
Real-time alerts, metrics tracking, and dashboard analytics.

Task #5: Monitoring Layer
- Alert System: Email, webhook, Slack, Discord, Telegram notifications
- Dashboard Metrics: System health, detection stats, performance tracking
- Historical Analysis: Trend analysis, user activity tracking
"""

from .alert_system import AlertSystem, AlertPriority, AlertChannel
from .dashboard_metrics import DashboardMetrics

__all__ = [
    'AlertSystem',
    'AlertPriority',
    'AlertChannel',
    'DashboardMetrics'
]
