"""Webhook support for deployment notifications."""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class WebhookSender:
    """Send webhook notifications for deployment events."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def send(
        self, event: str, data: Dict[str, Any], webhook_url: Optional[str] = None
    ) -> bool:
        """Send webhook notification.

        Args:
            event: Event type (e.g., 'deployment.success', 'deployment.failed')
            data: Event data
            webhook_url: Override default webhook URL

        Returns:
            True if webhook sent successfully, False otherwise
        """
        url = webhook_url or self.webhook_url
        if not url:
            logger.warning("No webhook URL configured")
            return False

        payload = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Webhook sent successfully: {event}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    def deployment_started(self, host: str, **kwargs):
        """Send deployment started event."""
        return self.send("deployment.started", {"host": host, **kwargs})

    def deployment_success(self, host: str, duration: float, **kwargs):
        """Send deployment success event."""
        return self.send(
            "deployment.success", {"host": host, "duration_seconds": duration, **kwargs}
        )

    def deployment_failed(self, host: str, error: str, **kwargs):
        """Send deployment failed event."""
        return self.send("deployment.failed", {"host": host, "error": error, **kwargs})

    def rollback_started(self, host: str, **kwargs):
        """Send rollback started event."""
        return self.send("rollback.started", {"host": host, **kwargs})

    def rollback_success(self, host: str, **kwargs):
        """Send rollback success event."""
        return self.send("rollback.success", {"host": host, **kwargs})

    def health_check_failed(self, host: str, check_type: str, **kwargs):
        """Send health check failed event."""
        return self.send(
            "health_check.failed", {"host": host, "check_type": check_type, **kwargs}
        )
