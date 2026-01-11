"""Drift detection to catch manual server changes."""

import hashlib
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detects configuration drift on deployed servers."""

    def __init__(self, state_dir: Optional[Path] = None):
        if state_dir is None:
            state_dir = Path.home() / ".vm_tool"
        self.state_dir = state_dir
        self.drift_file = self.state_dir / "drift_state.json"
        self._ensure_state_dir()

    def _ensure_state_dir(self):
        """Create state directory if it doesn't exist."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load_drift_state(self) -> Dict:
        """Load drift state from file."""
        if not self.drift_file.exists():
            return {}
        try:
            with open(self.drift_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Invalid drift state file")
            return {}

    def _save_drift_state(self, state: Dict):
        """Save drift state to file."""
        with open(self.drift_file, "w") as f:
            json.dump(state, f, indent=2)

    def record_file_state(self, host: str, file_path: str, content_hash: str):
        """Record the expected state of a file."""
        state = self._load_drift_state()
        if host not in state:
            state[host] = {}
        state[host][file_path] = content_hash
        self._save_drift_state(state)

    def check_drift(self, host: str, user: str = "ubuntu") -> List[Dict]:
        """Check for drift on a host."""
        state = self._load_drift_state()
        if host not in state:
            logger.info(f"No baseline state for {host}")
            return []

        drifts = []
        for file_path, expected_hash in state[host].items():
            actual_hash = self._get_remote_file_hash(host, user, file_path)
            if actual_hash and actual_hash != expected_hash:
                drifts.append(
                    {
                        "file": file_path,
                        "expected": expected_hash,
                        "actual": actual_hash,
                        "status": "modified",
                    }
                )
            elif not actual_hash:
                drifts.append(
                    {
                        "file": file_path,
                        "expected": expected_hash,
                        "actual": None,
                        "status": "deleted",
                    }
                )

        return drifts

    def _get_remote_file_hash(
        self, host: str, user: str, file_path: str
    ) -> Optional[str]:
        """Get hash of a file on remote server."""
        try:
            result = subprocess.run(
                ["ssh", f"{user}@{host}", f"sha256sum {file_path}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # sha256sum output: "hash  filename"
                return result.stdout.split()[0]
        except Exception as e:
            logger.error(f"Failed to get remote file hash: {e}")
        return None
