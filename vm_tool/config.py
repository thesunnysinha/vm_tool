"""Configuration management for vm_tool."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Config:
    """Manages vm_tool configuration and profiles."""

    def __init__(self):
        self.config_dir = Path.home() / ".vm_tool"
        self.config_file = self.config_dir / "config.json"
        self.profiles_file = self.config_dir / "profiles.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON config file."""
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {file_path}, returning empty config")
            return {}

    def _save(self, data: Dict[str, Any], file_path: Path):
        """Save data to JSON config file."""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        config = self._load(self.config_file)
        config[key] = value
        self._save(config, self.config_file)
        logger.info(f"Set config: {key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        config = self._load(self.config_file)
        return config.get(key, default)

    def unset(self, key: str):
        """Remove a configuration value."""
        config = self._load(self.config_file)
        if key in config:
            del config[key]
            self._save(config, self.config_file)
            logger.info(f"Unset config: {key}")
        else:
            logger.warning(f"Config key not found: {key}")

    def list_all(self) -> Dict[str, Any]:
        """List all configuration values."""
        return self._load(self.config_file)

    # Profile management
    def create_profile(self, name: str, environment: str = "development", **kwargs):
        """Create a deployment profile with environment tag."""
        profiles = self._load(self.profiles_file)
        profile_data = {"environment": environment, **kwargs}
        profiles[name] = profile_data
        self._save(profiles, self.profiles_file)
        logger.info(f"Created profile: {name} (environment: {environment})")

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a deployment profile."""
        profiles = self._load(self.profiles_file)
        return profiles.get(name)

    def list_profiles(self) -> Dict[str, Dict[str, Any]]:
        """List all profiles."""
        return self._load(self.profiles_file)

    def delete_profile(self, name: str):
        """Delete a deployment profile."""
        profiles = self._load(self.profiles_file)
        if name in profiles:
            del profiles[name]
            self._save(profiles, self.profiles_file)
            logger.info(f"Deleted profile: {name}")
        else:
            logger.warning(f"Profile not found: {name}")
