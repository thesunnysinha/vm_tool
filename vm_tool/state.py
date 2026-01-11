"""State management for idempotent deployments."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DeploymentState:
    """Manages deployment state for idempotency."""

    def __init__(self, state_dir: Optional[Path] = None):
        if state_dir is None:
            state_dir = Path.home() / ".vm_tool"
        self.state_dir = state_dir
        self.state_file = self.state_dir / "deployment_state.json"
        self._ensure_state_dir()

    def _ensure_state_dir(self):
        """Create state directory if it doesn't exist."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> Dict[str, Any]:
        """Load deployment state from file."""
        if not self.state_file.exists():
            return {}
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Invalid state file, returning empty state")
            return {}

    def _save_state(self, state: Dict[str, Any]):
        """Save deployment state to file."""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def compute_hash(self, compose_file: str) -> str:
        """Compute hash of docker-compose file for change detection."""
        try:
            with open(compose_file, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            logger.warning(f"Compose file not found: {compose_file}")
            return ""

    def record_deployment(
        self,
        host: str,
        compose_file: str,
        compose_hash: str,
        service_name: str = "default",
    ):
        """Record a successful deployment."""
        state = self._load_state()

        if host not in state:
            state[host] = {}

        state[host][service_name] = {
            "compose_file": compose_file,
            "compose_hash": compose_hash,
            "deployed_at": datetime.now().isoformat(),
            "status": "deployed",
        }

        self._save_state(state)
        logger.info(f"Recorded deployment: {host}/{service_name}")

    def get_deployment(
        self, host: str, service_name: str = "default"
    ) -> Optional[Dict]:
        """Get deployment info for a host/service."""
        state = self._load_state()
        return state.get(host, {}).get(service_name)

    def needs_update(
        self, host: str, compose_hash: str, service_name: str = "default"
    ) -> bool:
        """Check if deployment needs update based on compose file hash."""
        deployment = self.get_deployment(host, service_name)

        if not deployment:
            logger.info(f"No previous deployment found for {host}/{service_name}")
            return True

        previous_hash = deployment.get("compose_hash")
        if previous_hash != compose_hash:
            logger.info(
                f"Compose file changed for {host}/{service_name} "
                f"(old: {previous_hash[:8]}, new: {compose_hash[:8]})"
            )
            return True

        logger.info(f"No changes detected for {host}/{service_name}")
        return False

    def mark_failed(self, host: str, service_name: str = "default", error: str = ""):
        """Mark a deployment as failed."""
        state = self._load_state()

        if host not in state:
            state[host] = {}

        if service_name in state[host]:
            state[host][service_name]["status"] = "failed"
            state[host][service_name]["error"] = error
            state[host][service_name]["failed_at"] = datetime.now().isoformat()
        else:
            state[host][service_name] = {
                "status": "failed",
                "error": error,
                "failed_at": datetime.now().isoformat(),
            }

        self._save_state(state)
        logger.error(f"Marked deployment as failed: {host}/{service_name}")
