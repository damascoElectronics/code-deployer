#!/usr/bin/env python3
"""
Central Notification Manager
Orchestrates all notification channels (email, Slack, Teams, webhooks)
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from notifications.email_notifier import EmailNotifier
from notifications.slack_notifier import SlackNotifier
from notifications.teams_notifier import TeamsNotifier
from notifications.webhook_notifier import WebhookNotifier
from common.logger import get_logger
from common.config_loader import load_config

logger = get_logger(__name__)

class NotificationManager:
    """Central manager for all notification channels"""
    
    def __init__(self, config_path: str = "config/notification-config.json"):
        """Initialize notification manager"""
        self.config = load_config(config_path)
        self.notifiers = self._initialize_notifiers()
        
    def _initialize_notifiers(self) -> Dict[str, Any]:
        """Initialize all configured notifiers"""
        notifiers = {}
        
        # Email notifier
        if self.config.get('email', {}).get('enabled', False):
            notifiers['email'] = EmailNotifier(self.config['email'])
        
        # Slack notifier
        if self.config.get('slack', {}).get('enabled', False):
            notifiers['slack'] = SlackNotifier(self.config['slack'])
        
        # Teams notifier
        if self.config.get('teams', {}).get('enabled', False):
            notifiers['teams'] = TeamsNotifier(self.config['teams'])
        
        # Webhook notifier
        if self.config.get('webhooks', {}).get('enabled', False):
            notifiers['webhooks'] = WebhookNotifier(self.config['webhooks'])
        
        logger.info(f"📧 Initialized {len(notifiers)} notification channels: {list(notifiers.keys())}")
        return notifiers
    
    def send_quality_notification(self, quality_summary: Dict[str, Any], 
                                 notification_type: str = "scan_complete") -> bool:
        """Send quality scan notifications"""
        logger.info(f"📧 Sending quality notifications: {notification_type}")
        
        # Determine notification priority and channels
        priority = self._determine_quality_priority(quality_summary)
        channels = self._get_channels_for_priority(priority, 'quality')
        
        success_count = 0
        
        for channel_name in channels:
            if channel_name in self.notifiers:
                try:
                    notifier = self.notifiers[channel_name]
                    success = notifier.send_quality_notification(quality_summary, notification_type)
                    if success:
                        success_count += 1
                        logger.info(f"✅ Quality notification sent via {channel_name}")
                    else:
                        logger.warning(f"⚠️ Failed to send quality notification via {channel_name}")
                except Exception as e:
                    logger.error(f"❌ Error sending quality notification via {channel_name}: {e}")
        
        return success_count > 0
    
    def send_security_notification(self, security_summary: Dict[str, Any], 
                                  notification_type: str = "scan_complete") -> bool:
        """Send security scan notifications"""
        logger.info(f"🔒 Sending security notifications: {notification_type}")
        
        # Determine notification priority and channels
        priority = self._determine_security_priority(security_summary)
        channels = self._get_channels_for_priority(priority, 'security')
        
        success_count = 0
        
        for channel_name in channels:
            if channel_name in self.notifiers:
                try:
                    notifier = self.notifiers[channel_name]
                    success = notifier.send_security_notification(security_summary, notification_type)
                    if success:
                        success_count += 1
                        logger.info(f"✅ Security notification sent via {channel_name}")
                    else:
                        logger.warning(f"⚠️ Failed to send security notification via {channel_name}")
                except Exception as e:
                    logger.error(f"❌ Error sending security notification via {channel_name}: {e}")
        
        return success_count > 0
    
    def send_combined_notification(self, quality_summary: Dict[str, Any], 
                                  security_summary: Dict[str, Any],
                                  notification_type: str = "weekly_report") -> bool:
        """Send combined quality and security notifications"""
        logger.info(f"📊 Sending combined notifications: {notification_type}")
        
        # Determine overall priority
        quality_priority = self._determine_quality_priority(quality_summary)
        security_priority = self._determine_security_priority(security_summary)
        overall_priority = max(quality_priority, security_priority)
        
        channels = self._get_channels_for_priority(overall_priority, 'combined')
        success_count = 0
        
        for channel_name in channels:
            if channel_name in self.notifiers:
                try:
                    notifier = self.notifiers[channel_name]
                    success = notifier.send_combined_notification(
                        quality_summary, security_summary, notification_type
                    )
                    if success:
                        success_count += 1
                        logger.info(f"✅ Combined notification sent via {channel_name}")
                    else:
                        logger.warning(f"⚠️ Failed to send combined notification via {channel_name}")
                except Exception as e:
                    logger.error(f"❌ Error sending combined notification via {channel_name}: {e}")
        
        return success_count > 0
    
    def _determine_quality_priority(self, quality_summary: Dict[str, Any]) -> int:
        """Determine notification priority for quality issues (1=low, 2=medium, 3=high)"""
        if 'error' in quality_summary:
            return 1  # Low priority for failed scans
        
        severity_breakdown = quality_summary.get('severity_breakdown', {})
        errors = severity_breakdown.get('error', 0)
        warnings = severity_breakdown.get('warning', 0)
        quality_score = quality_summary.get('quality_score', 100)
        
        if errors > 0 or quality_score < 50:
            return 3  # High priority
        elif warnings > 10 or quality_score < 80:
            return 2  # Medium priority
        else:
            return 1  # Low priority
    
    def _determine_security_priority(self, security_summary: Dict[str, Any]) -> int:
        """Determine notification priority for security issues (1=low, 2=medium, 3=high)"""
        if 'error' in security_summary:
            return 1  # Low priority for failed scans
        
        vulnerability_breakdown = security_summary.get('vulnerability_breakdown', {})
        critical = vulnerability_breakdown.get('critical', 0)
        high = vulnerability_breakdown.get('high', 0)
        medium = vulnerability_breakdown.get('medium', 0)
        
        if critical > 0:
            return 3  # High priority
        elif high > 0 or medium > 5:
            return 2  # Medium priority
        else:
            return 1  # Low priority
    
    def _get_channels_for_priority(self, priority: int, scan_type: str) -> List[str]:
        """Get notification channels based on priority and scan type"""
        config_key = f"{scan_type}_notifications"
        notification_config = self.config.get(config_key, {})
        
        if priority == 3:  # High priority
            return notification_config.get('high_priority', ['email', 'slack'])
        elif priority == 2:  # Medium priority
            return notification_config.get('medium_priority', ['email'])
        else:  # Low priority
            return notification_config.get('low_priority', ['email'])

def main():
    """Main entry point for testing notifications"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Send test notifications")
    parser.add_argument("--type", choices=["quality", "security", "combined"], 
                       required=True, help="Type of notification to send")
    parser.add_argument("--test", action="store_true", help="Send test notification")
    
    args = parser.parse_args()
    
    if not args.test:
        logger.error("Use --test flag to send test notifications")
        return 1
    
    manager = NotificationManager()
    
    # Sample test data
    test_quality_summary = {
        'scan_id': 'test-quality-123',
        'timestamp': datetime.now().isoformat(),
        'quality_score': 85.5,
        'files_analyzed': 10,
        'total_issues': 5,
        'severity_breakdown': {'error': 0, 'warning': 3, 'info': 2}
    }
    
    test_security_summary = {
        'scan_id': 'test-security-456',
        'timestamp': datetime.now().isoformat(),
        'packages_scanned': 25,
        'total_vulnerabilities': 2,
        'vulnerability_breakdown': {'critical': 0, 'high': 1, 'medium': 1, 'low': 0}
    }
    
    try:
        if args.type == "quality":
            success = manager.send_quality_notification(test_quality_summary, "test")
        elif args.type == "security":
            success = manager.send_security_notification(test_security_summary, "test")
        elif args.type == "combined":
            success = manager.send_combined_notification(
                test_quality_summary, test_security_summary, "test"
            )
        
        if success:
            logger.info("✅ Test notification sent successfully")
            return 0
        else:
            logger.error("❌ Failed to send test notification")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test notification failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())