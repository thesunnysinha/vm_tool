"""Backup and restore functionality for disaster recovery."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backups and restores for deployed services."""

    def __init__(self, backup_dir: Optional[Path] = None):
        if backup_dir is None:
            backup_dir = Path.home() / ".vm_tool" / "backups"
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        host: str,
        user: str,
        paths: List[str],
        include_volumes: bool = False,
        include_db: bool = False,
    ) -> str:
        """Create a backup of specified paths on remote host."""
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{host}_{backup_id}.tar.gz"

        logger.info(f"Creating backup: {backup_id}")

        # Build tar command
        tar_paths = " ".join(paths)
        remote_backup = f"/tmp/backup_{backup_id}.tar.gz"  # nosec B108

        try:
            # Create tar on remote
            tar_cmd = f"tar -czf {remote_backup} {tar_paths}"
            result = subprocess.run(
                ["ssh", f"{user}@{host}", tar_cmd],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Backup creation failed: {result.stderr}")

            # Download backup
            subprocess.run(
                ["scp", f"{user}@{host}:{remote_backup}", str(backup_path)],
                check=True,
                timeout=300,
            )

            # Cleanup remote backup
            subprocess.run(["ssh", f"{user}@{host}", f"rm {remote_backup}"], timeout=30)

            # Save metadata
            metadata = {
                "id": backup_id,
                "host": host,
                "paths": paths,
                "timestamp": datetime.now().isoformat(),
                "size": backup_path.stat().st_size,
            }
            metadata_file = self.backup_dir / f"{host}_{backup_id}.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"✅ Backup created: {backup_id}")
            return backup_id

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    def list_backups(self, host: Optional[str] = None) -> List[Dict]:
        """List available backups."""
        backups = []
        for metadata_file in self.backup_dir.glob("*.json"):
            with open(metadata_file, "r") as f:
                backup = json.load(f)
                if host is None or backup["host"] == host:
                    backups.append(backup)

        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

    def restore_backup(self, backup_id: str, host: str, user: str):
        """Restore a backup to the specified host."""
        # Find backup file
        backup_files = list(self.backup_dir.glob(f"*_{backup_id}.tar.gz"))
        if not backup_files:
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        backup_file = backup_files[0]
        remote_backup = f"/tmp/restore_{backup_id}.tar.gz"  # nosec B108

        try:
            # Upload backup
            subprocess.run(
                ["scp", str(backup_file), f"{user}@{host}:{remote_backup}"],
                check=True,
                timeout=300,
            )

            # Extract on remote
            subprocess.run(
                ["ssh", f"{user}@{host}", f"tar -xzf {remote_backup} -C /"],
                check=True,
                timeout=300,
            )

            # Cleanup
            subprocess.run(["ssh", f"{user}@{host}", f"rm {remote_backup}"], timeout=30)

            logger.info(f"✅ Backup restored: {backup_id}")

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
