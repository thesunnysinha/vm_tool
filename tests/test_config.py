"""Tests for configuration management."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vm_tool.config import Config


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    with patch("vm_tool.config.Path.home", return_value=tmp_path):
        yield tmp_path / ".vm_tool"


def test_config_set_and_get(temp_config_dir):
    """Test setting and getting config values."""
    config = Config()
    config.set("default-host", "192.168.1.100")
    config.set("default-user", "ubuntu")

    assert config.get("default-host") == "192.168.1.100"
    assert config.get("default-user") == "ubuntu"
    assert config.get("nonexistent") is None
    assert config.get("nonexistent", "default") == "default"


def test_config_unset(temp_config_dir):
    """Test unsetting config values."""
    config = Config()
    config.set("test-key", "test-value")
    assert config.get("test-key") == "test-value"

    config.unset("test-key")
    assert config.get("test-key") is None


def test_config_list_all(temp_config_dir):
    """Test listing all config values."""
    config = Config()
    config.set("key1", "value1")
    config.set("key2", "value2")

    all_config = config.list_all()
    assert all_config == {"key1": "value1", "key2": "value2"}


def test_create_profile(temp_config_dir):
    """Test creating a deployment profile."""
    config = Config()
    config.create_profile(
        "staging",
        environment="staging",
        host="10.0.1.5",
        user="deploy",
        compose_file="docker-compose.yml",
    )

    profile = config.get_profile("staging")
    assert profile == {
        "environment": "staging",
        "host": "10.0.1.5",
        "user": "deploy",
        "compose_file": "docker-compose.yml",
    }


def test_list_profiles(temp_config_dir):
    """Test listing all profiles."""
    config = Config()
    config.create_profile(
        "staging", environment="staging", host="10.0.1.5", user="deploy"
    )
    config.create_profile(
        "production", environment="production", host="10.0.2.10", user="prod"
    )

    profiles = config.list_profiles()
    assert "staging" in profiles
    assert "production" in profiles
    assert profiles["staging"]["host"] == "10.0.1.5"
    assert profiles["staging"]["environment"] == "staging"


def test_delete_profile(temp_config_dir):
    """Test deleting a profile."""
    config = Config()
    config.create_profile("test-profile", host="1.2.3.4")

    assert config.get_profile("test-profile") is not None

    config.delete_profile("test-profile")
    assert config.get_profile("test-profile") is None


def test_config_persistence(temp_config_dir):
    """Test that config persists across instances."""
    config1 = Config()
    config1.set("persistent-key", "persistent-value")

    config2 = Config()
    assert config2.get("persistent-key") == "persistent-value"


def test_invalid_json_handling(temp_config_dir):
    """Test handling of invalid JSON in config file."""
    config = Config()
    config_file = config.config_file

    # Write invalid JSON
    with open(config_file, "w") as f:
        f.write("invalid json {")

    # Should return empty dict instead of crashing
    assert config.list_all() == {}
