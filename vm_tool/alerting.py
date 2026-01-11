"""Alerting system with multiple notification channels."""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert message."""

    title: str
    message: str
    severity: AlertSeverity
    metadata: Optional[Dict[str, Any]] = None


class AlertChannel:
    """Base class for alert channels."""

    def send(self, alert: Alert) -> bool:
        """Send alert through this channel."""
        raise NotImplementedError


class SlackAlertChannel(AlertChannel):
    """Send alerts to Slack."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        import requests

        # Color based on severity
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#8b0000",
        }

        payload = {
            "attachments": [
                {
                    "color": colors.get(alert.severity, "#808080"),
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True,
                        }
                    ],
                }
            ]
        }

        if alert.metadata:
            for key, value in alert.metadata.items():
                payload["attachments"][0]["fields"].append(
                    {
                        "title": key.replace("_", " ").title(),
                        "value": str(value),
                        "short": True,
                    }
                )

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Alert sent to Slack")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


class PagerDutyAlertChannel(AlertChannel):
    """Send alerts to PagerDuty."""

    def __init__(self, integration_key: str):
        self.integration_key = integration_key

    def send(self, alert: Alert) -> bool:
        """Send alert to PagerDuty."""
        import requests

        # Map severity to PagerDuty severity
        severity_map = {
            AlertSeverity.INFO: "info",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "error",
            AlertSeverity.CRITICAL: "critical",
        }

        payload = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "payload": {
                "summary": alert.title,
                "severity": severity_map.get(alert.severity, "error"),
                "source": "vm-tool",
                "custom_details": alert.metadata or {},
            },
        }

        try:
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue", json=payload
            )
            response.raise_for_status()
            logger.info("Alert sent to PagerDuty")
            return True
        except Exception as e:
            logger.error(f"Failed to send PagerDuty alert: {e}")
            return False


class SMSAlertChannel(AlertChannel):
    """Send alerts via SMS using Twilio."""

    def __init__(
        self, account_sid: str, auth_token: str, from_number: str, to_numbers: List[str]
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_numbers = to_numbers

    def send(self, alert: Alert) -> bool:
        """Send alert via SMS."""
        try:
            from twilio.rest import Client

            client = Client(self.account_sid, self.auth_token)

            # Format message
            message = f"[{alert.severity.value.upper()}] {alert.title}\n{alert.message}"

            # Send to all numbers
            for number in self.to_numbers:
                client.messages.create(body=message, from_=self.from_number, to=number)

            logger.info(f"Alert sent via SMS to {len(self.to_numbers)} recipients")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
            return False


class EmailAlertChannel(AlertChannel):
    """Send alerts via email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        from_email: str,
        to_emails: List[str],
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_emails = to_emails
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def send(self, alert: Alert) -> bool:
        """Send alert via email."""
        from vm_tool.notifications import EmailNotifier

        notifier = EmailNotifier(
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
            smtp_user=self.smtp_user,
            smtp_password=self.smtp_password,
            from_email=self.from_email,
        )

        subject = f"[{alert.severity.value.upper()}] {alert.title}"

        return notifier.send_email(
            to_emails=self.to_emails, subject=subject, body=alert.message
        )


class AlertingSystem:
    """Centralized alerting system."""

    def __init__(self):
        self.channels: List[AlertChannel] = []

    def add_channel(self, channel: AlertChannel):
        """Add an alert channel."""
        self.channels.append(channel)

    def send_alert(self, alert: Alert):
        """Send alert through all channels."""
        logger.info(f"Sending alert: {alert.title} ({alert.severity.value})")

        for channel in self.channels:
            try:
                channel.send(alert)
            except Exception as e:
                logger.error(f"Failed to send alert through channel: {e}")

    def deployment_failed(self, host: str, error: str, **metadata):
        """Send deployment failure alert."""
        alert = Alert(
            title="Deployment Failed",
            message=f"Deployment to {host} failed: {error}",
            severity=AlertSeverity.ERROR,
            metadata={"host": host, "error": error, **metadata},
        )
        self.send_alert(alert)

    def deployment_succeeded(self, host: str, duration: float, **metadata):
        """Send deployment success notification."""
        alert = Alert(
            title="Deployment Successful",
            message=f"Deployment to {host} completed in {duration:.2f}s",
            severity=AlertSeverity.INFO,
            metadata={"host": host, "duration": duration, **metadata},
        )
        self.send_alert(alert)

    def health_check_failed(self, host: str, check_type: str, **metadata):
        """Send health check failure alert."""
        alert = Alert(
            title="Health Check Failed",
            message=f"Health check '{check_type}' failed on {host}",
            severity=AlertSeverity.WARNING,
            metadata={"host": host, "check_type": check_type, **metadata},
        )
        self.send_alert(alert)

    def critical_error(self, title: str, message: str, **metadata):
        """Send critical error alert."""
        alert = Alert(
            title=title,
            message=message,
            severity=AlertSeverity.CRITICAL,
            metadata=metadata,
        )
        self.send_alert(alert)


# Global alerting system instance
_alerting_system = None


def get_alerting_system() -> AlertingSystem:
    """Get global alerting system instance."""
    global _alerting_system
    if _alerting_system is None:
        _alerting_system = AlertingSystem()
    return _alerting_system
