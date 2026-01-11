"""Deployment history tracking and rollback functionality."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DeploymentHistory:
    """Manages deployment history for rollback capability."""

    def __init__(self, history_dir: Optional[Path] = None):
        if history_dir is None:
            history_dir = Path.home() / ".vm_tool"
        self.history_dir = history_dir
        self.history_file = self.history_dir / "deployment_history.json"
        self._ensure_history_dir()

    def _ensure_history_dir(self):
        """Create history directory if it doesn't exist."""
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load deployment history from file."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Invalid history file, returning empty history")
            return []

    def _save_history(self, history: List[Dict[str, Any]]):
        """Save deployment history to file."""
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

    def record_deployment(
        self,
        host: str,
        compose_file: str,
        compose_hash: str,
        git_commit: Optional[str] = None,
        service_name: str = "default",
        status: str = "success",
        error: Optional[str] = None,
    ) -> str:
        """Record a deployment in history and return deployment ID."""
        history = self._load_history()

        deployment_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        deployment_record = {
            "id": deployment_id,
            "timestamp": datetime.now().isoformat(),
            "host": host,
            "service_name": service_name,
            "compose_file": compose_file,
            "compose_hash": compose_hash,
            "git_commit": git_commit,
            "status": status,
            "error": error,
        }

        history.append(deployment_record)

        # Keep only last 100 deployments
        if len(history) > 100:
            history = history[-100:]

        self._save_history(history)
        logger.info(f"Recorded deployment: {deployment_id}")

        return deployment_id

    def get_history(
        self, host: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get deployment history, optionally filtered by host."""
        history = self._load_history()

        if host:
            history = [d for d in history if d.get("host") == host]

        # Return most recent first
        history.reverse()

        return history[:limit]

    def get_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific deployment by ID."""
        history = self._load_history()
        for deployment in history:
            if deployment.get("id") == deployment_id:
                return deployment
        return None

    def get_previous_deployment(
        self, host: str, service_name: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """Get the previous successful deployment for a host/service."""
        history = self._load_history()

        # Filter by host and service, get successful deployments
        matching = [
            d
            for d in history
            if d.get("host") == host
            and d.get("service_name") == service_name
            and d.get("status") == "success"
        ]

        if len(matching) >= 2:
            # Return second-to-last (previous deployment)
            return matching[-2]

        return None

    def get_rollback_info(
        self, host: str, deployment_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get rollback information for a deployment."""
        if deployment_id:
            return self.get_deployment(deployment_id)
        else:
            # Get previous deployment
            return self.get_previous_deployment(host)
