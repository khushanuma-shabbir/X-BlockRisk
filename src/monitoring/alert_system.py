"""
Real-time Alert System
Sends notifications for high-risk detections and system anomalies.

Production Features:
- Email alerts for high-risk addresses
- Webhook notifications for integrations
- Slack/Discord/Telegram support
- Alert throttling to prevent spam
- Priority-based routing
"""

import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    SMS = "sms"


class AlertThrottler:
    """
    Prevents alert spam by throttling repeated alerts
    """
    
    def __init__(self, cooldown_minutes: int = 60):
        """
        Initialize throttler
        
        Args:
            cooldown_minutes: Minutes to wait before re-sending same alert
        """
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.alert_history = {}  # {alert_key: last_sent_time}
    
    def should_send(self, alert_key: str) -> bool:
        """
        Check if alert should be sent
        
        Args:
            alert_key: Unique identifier for alert type
        
        Returns:
            bool indicating if alert should be sent
        """
        now = datetime.now()
        
        if alert_key not in self.alert_history:
            self.alert_history[key] = now
            return True
        
        last_sent = self.alert_history[alert_key]
        time_since = now - last_sent
        
        if time_since >= self.cooldown:
            self.alert_history[alert_key] = now
            return True
        
        logger.debug(f"Alert throttled: {alert_key} (sent {time_since.seconds//60}min ago)")
        return False


class AlertSystem:
    """
    Real-time alert notification system
    """
    
    def __init__(self):
        """Initialize alert system with environment config"""
        self.throttler = AlertThrottler(cooldown_minutes=60)
        
        # Load configuration from environment
        self.config = {
            'email': {
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'sender_email': os.getenv('ALERT_EMAIL_FROM', ''),
                'sender_password': os.getenv('ALERT_EMAIL_PASSWORD', ''),
                'recipient_emails': os.getenv('ALERT_EMAIL_TO', '').split(',')
            },
            'webhook': {
                'url': os.getenv('ALERT_WEBHOOK_URL', '')
            },
            'slack': {
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL', '')
            },
            'discord': {
                'webhook_url': os.getenv('DISCORD_WEBHOOK_URL', '')
            },
            'telegram': {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
                'chat_id': os.getenv('TELEGRAM_CHAT_ID', '')
            }
        }
    
    def send_alert(
        self,
        title: str,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        channels: Optional[List[AlertChannel]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """
        Send alert through specified channels
        
        Args:
            title: Alert title
            message: Alert message body
            priority: Alert priority level
            channels: List of channels to send to (default: all configured)
            metadata: Additional context data
        
        Returns:
            dict mapping channel to success status
        """
        # Create alert key for throttling
        alert_key = f"{title}:{priority.value}"
        
        # Check throttling
        if not self.throttler.should_send(alert_key):
            logger.info(f"Alert throttled: {title}")
            return {'throttled': True}
        
        # Default to all configured channels
        if channels is None:
            channels = [
                AlertChannel.EMAIL,
                AlertChannel.WEBHOOK,
                AlertChannel.SLACK
            ]
        
        results = {}
        
        # Send through each channel
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    results['email'] = self._send_email(title, message, priority, metadata)
                elif channel == AlertChannel.WEBHOOK:
                    results['webhook'] = self._send_webhook(title, message, priority, metadata)
                elif channel == AlertChannel.SLACK:
                    results['slack'] = self._send_slack(title, message, priority, metadata)
                elif channel == AlertChannel.DISCORD:
                    results['discord'] = self._send_discord(title, message, priority, metadata)
                elif channel == AlertChannel.TELEGRAM:
                    results['telegram'] = self._send_telegram(title, message, priority, metadata)
            except Exception as e:
                logger.error(f"Error sending {channel.value} alert: {e}")
                results[channel.value] = False
        
        return results
    
    def _send_email(
        self,
        title: str,
        message: str,
        priority: AlertPriority,
        metadata: Optional[Dict]
    ) -> bool:
        """Send email alert"""
        config = self.config['email']
        
        if not config['sender_email'] or not config['recipient_emails']:
            logger.warning("Email not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{priority.value.upper()}] {title}"
            msg['From'] = config['sender_email']
            msg['To'] = ', '.join(config['recipient_emails'])
            
            # HTML body
            html = f"""
            <html>
              <body>
                <h2 style="color: {'#d32f2f' if priority in [AlertPriority.HIGH, AlertPriority.CRITICAL] else '#ff6f00'};">
                  {title}
                </h2>
                <p>{message}</p>
                {self._format_metadata_html(metadata) if metadata else ''}
                <hr>
                <p style="color: #666; font-size: 12px;">
                  Sent by Fraud Detection System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send via SMTP
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['sender_email'], config['sender_password'])
                server.send_message(msg)
            
            logger.info(f"✓ Email alert sent: {title}")
            return True
        
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False
    
    def _send_webhook(
        self,
        title: str,
        message: str,
        priority: AlertPriority,
        metadata: Optional[Dict]
    ) -> bool:
        """Send generic webhook alert"""
        webhook_url = self.config['webhook']['url']
        
        if not webhook_url:
            return False
        
        try:
            payload = {
                'title': title,
                'message': message,
                'priority': priority.value,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            success = response.status_code == 200
            
            if success:
                logger.info(f"✓ Webhook alert sent: {title}")
            else:
                logger.warning(f"Webhook returned {response.status_code}")
            
            return success
        
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")
            return False
    
    def _send_slack(
        self,
        title: str,
        message: str,
        priority: AlertPriority,
        metadata: Optional[Dict]
    ) -> bool:
        """Send Slack alert"""
        webhook_url = self.config['slack']['webhook_url']
        
        if not webhook_url:
            return False
        
        try:
            # Color based on priority
            color_map = {
                AlertPriority.LOW: '#36a64f',
                AlertPriority.MEDIUM: '#ff6f00',
                AlertPriority.HIGH: '#d32f2f',
                AlertPriority.CRITICAL: '#b71c1c'
            }
            
            payload = {
                'attachments': [{
                    'color': color_map[priority],
                    'title': title,
                    'text': message,
                    'fields': self._format_metadata_slack(metadata) if metadata else [],
                    'footer': 'Fraud Detection System',
                    'ts': int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                logger.info(f"✓ Slack alert sent: {title}")
            
            return success
        
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False
    
    def _send_discord(
        self,
        title: str,
        message: str,
        priority: AlertPriority,
        metadata: Optional[Dict]
    ) -> bool:
        """Send Discord alert"""
        webhook_url = self.config['discord']['webhook_url']
        
        if not webhook_url:
            return False
        
        try:
            # Color based on priority (decimal format for Discord)
            color_map = {
                AlertPriority.LOW: 3581519,      # Green
                AlertPriority.MEDIUM: 16750592,  # Orange
                AlertPriority.HIGH: 13828095,    # Red
                AlertPriority.CRITICAL: 12001052 # Dark red
            }
            
            embed = {
                'title': title,
                'description': message,
                'color': color_map[priority],
                'timestamp': datetime.now().isoformat(),
                'footer': {
                    'text': 'Fraud Detection System'
                }
            }
            
            if metadata:
                embed['fields'] = self._format_metadata_discord(metadata)
            
            payload = {'embeds': [embed]}
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            success = response.status_code == 204
            
            if success:
                logger.info(f"✓ Discord alert sent: {title}")
            
            return success
        
        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            return False
    
    def _send_telegram(
        self,
        title: str,
        message: str,
        priority: AlertPriority,
        metadata: Optional[Dict]
    ) -> bool:
        """Send Telegram alert"""
        config = self.config['telegram']
        
        if not config['bot_token'] or not config['chat_id']:
            return False
        
        try:
            # Format message with markdown
            priority_emoji = {
                AlertPriority.LOW: '🟢',
                AlertPriority.MEDIUM: '🟡',
                AlertPriority.HIGH: '🔴',
                AlertPriority.CRITICAL: '🚨'
            }
            
            text = f"{priority_emoji[priority]} *{title}*\n\n{message}"
            
            if metadata:
                text += "\n\n" + self._format_metadata_telegram(metadata)
            
            url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
            
            response = requests.post(
                url,
                json={
                    'chat_id': config['chat_id'],
                    'text': text,
                    'parse_mode': 'Markdown'
                },
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                logger.info(f"✓ Telegram alert sent: {title}")
            
            return success
        
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False
    
    # ===== FORMATTING HELPERS =====
    
    def _format_metadata_html(self, metadata: Dict) -> str:
        """Format metadata as HTML"""
        html = "<table style='border-collapse: collapse;'>"
        for key, value in metadata.items():
            html += f"<tr><td style='padding: 5px; font-weight: bold;'>{key}:</td><td style='padding: 5px;'>{value}</td></tr>"
        html += "</table>"
        return html
    
    def _format_metadata_slack(self, metadata: Dict) -> List[Dict]:
        """Format metadata as Slack fields"""
        return [
            {'title': key, 'value': str(value), 'short': True}
            for key, value in metadata.items()
        ]
    
    def _format_metadata_discord(self, metadata: Dict) -> List[Dict]:
        """Format metadata as Discord fields"""
        return [
            {'name': key, 'value': str(value), 'inline': True}
            for key, value in metadata.items()
        ]
    
    def _format_metadata_telegram(self, metadata: Dict) -> str:
        """Format metadata as Telegram text"""
        lines = [f"*{key}:* {value}" for key, value in metadata.items()]
        return "\n".join(lines)
    
    # ===== HIGH-LEVEL ALERT METHODS =====
    
    def alert_high_risk_address(
        self,
        address: str,
        risk_score: float,
        reasons: List[str],
        chain: str = 'ethereum'
    ):
        """
        Send alert for high-risk address detection
        
        Args:
            address: Wallet address
            risk_score: Risk score (0-100)
            reasons: List of risk reasons
            chain: Blockchain network
        """
        priority = AlertPriority.CRITICAL if risk_score >= 80 else AlertPriority.HIGH
        
        title = f"High Risk Address Detected: {risk_score}/100"
        message = (
            f"A high-risk wallet has been detected on {chain}.\n\n"
            f"Address: {address}\n"
            f"Risk Score: {risk_score}/100\n\n"
            f"Reasons:\n" + "\n".join(f"• {r}" for r in reasons[:5])
        )
        
        metadata = {
            'Address': address,
            'Chain': chain.upper(),
            'Risk Score': f"{risk_score}/100",
            'Category': 'High Risk' if risk_score < 80 else 'Critical Risk'
        }
        
        self.send_alert(
            title=title,
            message=message,
            priority=priority,
            metadata=metadata
        )
    
    def alert_system_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None
    ):
        """
        Send alert for system errors
        
        Args:
            error_type: Type of error
            error_message: Error description
            context: Additional context
        """
        title = f"System Error: {error_type}"
        message = f"An error occurred in the fraud detection system:\n\n{error_message}"
        
        self.send_alert(
            title=title,
            message=message,
            priority=AlertPriority.MEDIUM,
            metadata=context,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
        )
    
    def alert_api_rate_limit(
        self,
        api_name: str,
        remaining_quota: int
    ):
        """
        Send alert when API rate limit is approaching
        
        Args:
            api_name: Name of API service
            remaining_quota: Remaining requests
        """
        title = f"API Rate Limit Warning: {api_name}"
        message = (
            f"The {api_name} API is approaching its rate limit.\n\n"
            f"Remaining quota: {remaining_quota} requests"
        )
        
        self.send_alert(
            title=title,
            message=message,
            priority=AlertPriority.LOW,
            channels=[AlertChannel.EMAIL]
        )


# Example usage
if __name__ == '__main__':
    print("Real-time Alert System")
    print("="*60)
    
    alert_system = AlertSystem()
    
    # Test high-risk alert
    alert_system.alert_high_risk_address(
        address='0x1234567890abcdef1234567890abcdef12345678',
        risk_score=85,
        reasons=[
            'High transaction volume',
            'Connected to known scam addresses',
            'Unusual token transfer patterns'
        ],
        chain='ethereum'
    )
    
    print("\n✓ Alert System Ready")
    print("\nSupported Channels:")
    print("  ✓ Email (SMTP)")
    print("  ✓ Generic Webhook")
    print("  ✓ Slack")
    print("  ✓ Discord")
    print("  ✓ Telegram")
