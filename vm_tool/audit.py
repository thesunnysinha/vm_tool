"""Audit logging for all deployment operations."""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""

    DEPLOYMENT_STARTED = "deployment.started"
    DEPLOYMENT_SUCCESS = "deployment.success"
    DEPLOYMENT_FAILED = "deployment.failed"
    ROLLBACK_STARTED = "rollback.started"
    ROLLBACK_SUCCESS = "rollback.success"
    CONFIG_CHANGED = "config.changed"
    SECRET_ACCESSED = "secret.accessed"
    USER_LOGIN = "user.login"
    PERMISSION_DENIED = "permission.denied"


class AuditLogger:
    """Centralized audit logging system."""

    def __init__(self, audit_dir: str = ".vm_tool/audit"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.audit_dir / "audit.jsonl"

    def log_event(
        self,
        event_type: AuditEventType,
        user: str,
        action: str,
        resource: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an audit event."""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "user": user,
            "action": action,
            "resource": resource,
            "success": success,
            "metadata": metadata or {},
        }

        # Append to audit log
        with open(self.audit_file, "a") as f:
            f.write(json.dumps(event) + "\n")

        logger.info(
            f"Audit: {user} {action} {resource} - {'success' if success else 'failed'}"
        )

    def get_audit_trail(self, limit: int = 100) -> list:
        """Get recent audit events."""
        if not self.audit_file.exists():
            return []

        events = []
        with open(self.audit_file) as f:
            for line in f:
                events.append(json.loads(line))

        return events[-limit:]

    def search_events(
        self,
        user: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list:
        """Search audit events with filters."""
        events = self.get_audit_trail(limit=10000)

        filtered = []
        for event in events:
            if user and event.get("user") != user:
                continue
            if event_type and event.get("event_type") != event_type:
                continue
            if start_time:
                event_time = datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                )
                if event_time < start_time:
                    continue
            if end_time:
                event_time = datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                )
                if event_time > end_time:
                    continue

            filtered.append(event)

        return filtered


# Global audit logger
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
