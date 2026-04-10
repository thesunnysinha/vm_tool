"""Backup and restore functionality for disaster recovery."""

import json
import logging
import os
import shlex
import subprocess
import tempfile
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
        self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

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

        # Safely quote each path to prevent shell injection
        quoted_paths = " ".join(shlex.quote(p) for p in paths)
        # Use a non-predictable remote temp path scoped to the backup ID
        remote_backup = f"/tmp/vm_tool_backup_{backup_id}_{os.getpid()}.tar.gz"

        try:
            # Create tar on remote — quoted paths prevent injection
            tar_cmd = f"tar -czf {shlex.quote(remote_backup)} {quoted_paths}"
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

            # Cleanup remote backup — failure here is non-fatal, log it
            cleanup = subprocess.run(
                ["ssh", f"{user}@{host}", f"rm -f {shlex.quote(remote_backup)}"],
                timeout=30,
            )
            if cleanup.returncode != 0:
                logger.warning(f"Remote backup cleanup may have failed for {remote_backup}")

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

    def restore_backup(self, backup_id: str, host: str, user: str, restore_dir: str = "/"):
        """Restore a backup to the specified host.

        Args:
            backup_id: ID of the backup to restore.
            host: Target host.
            user: SSH user.
            restore_dir: Directory to extract into. Defaults to '/' to restore
                         absolute paths in-place. Override to restore to a staging
                         area (e.g. '/tmp/restore') for safety.
        """
        # Find backup file
        backup_files = list(self.backup_dir.glob(f"*_{backup_id}.tar.gz"))
        if not backup_files:
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        backup_file = backup_files[0]
        remote_backup = f"/tmp/vm_tool_restore_{backup_id}_{os.getpid()}.tar.gz"

        try:
            # Upload backup
            subprocess.run(
                ["scp", str(backup_file), f"{user}@{host}:{remote_backup}"],
                check=True,
                timeout=300,
            )

            # Extract on remote into restore_dir
            extract_cmd = (
                f"tar -xzf {shlex.quote(remote_backup)} -C {shlex.quote(restore_dir)}"
            )
            subprocess.run(
                ["ssh", f"{user}@{host}", extract_cmd],
                check=True,
                timeout=300,
            )

            # Cleanup
            cleanup = subprocess.run(
                ["ssh", f"{user}@{host}", f"rm -f {shlex.quote(remote_backup)}"],
                timeout=30,
            )
            if cleanup.returncode != 0:
                logger.warning(f"Remote restore file cleanup may have failed for {remote_backup}")

            logger.info(f"✅ Backup restored: {backup_id}")

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
