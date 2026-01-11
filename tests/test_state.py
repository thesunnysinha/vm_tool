"""Tests for idempotent deployments."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vm_tool.state import DeploymentState


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary state directory."""
    return tmp_path / ".vm_tool"


def test_compute_hash(temp_state_dir, tmp_path):
    """Test computing hash of compose file."""
    state = DeploymentState(temp_state_dir)

    # Create a test compose file
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("version: '3'\nservices:\n  web:\n    image: nginx")

    hash1 = state.compute_hash(str(compose_file))
    assert len(hash1) == 64  # SHA256 hash length

    # Same content should produce same hash
    hash2 = state.compute_hash(str(compose_file))
    assert hash1 == hash2

    # Different content should produce different hash
    compose_file.write_text("version: '3'\nservices:\n  web:\n    image: apache")
    hash3 = state.compute_hash(str(compose_file))
    assert hash1 != hash3


def test_record_and_get_deployment(temp_state_dir):
    """Test recording and retrieving deployment info."""
    state = DeploymentState(temp_state_dir)

    state.record_deployment(
        host="192.168.1.100",
        compose_file="docker-compose.yml",
        compose_hash="abc123",
        service_name="web",
    )

    deployment = state.get_deployment("192.168.1.100", "web")
    assert deployment is not None
    assert deployment["compose_file"] == "docker-compose.yml"
    assert deployment["compose_hash"] == "abc123"
    assert deployment["status"] == "deployed"
    assert "deployed_at" in deployment


def test_needs_update_no_previous_deployment(temp_state_dir):
    """Test needs_update with no previous deployment."""
    state = DeploymentState(temp_state_dir)

    # Should need update if no previous deployment
    assert state.needs_update("192.168.1.100", "abc123", "web") is True


def test_needs_update_same_hash(temp_state_dir):
    """Test needs_update with same hash."""
    state = DeploymentState(temp_state_dir)

    state.record_deployment(
        host="192.168.1.100",
        compose_file="docker-compose.yml",
        compose_hash="abc123",
        service_name="web",
    )

    # Should not need update if hash is same
    assert state.needs_update("192.168.1.100", "abc123", "web") is False


def test_needs_update_different_hash(temp_state_dir):
    """Test needs_update with different hash."""
    state = DeploymentState(temp_state_dir)

    state.record_deployment(
        host="192.168.1.100",
        compose_file="docker-compose.yml",
        compose_hash="abc123",
        service_name="web",
    )

    # Should need update if hash is different
    assert state.needs_update("192.168.1.100", "def456", "web") is True


def test_mark_failed(temp_state_dir):
    """Test marking deployment as failed."""
    state = DeploymentState(temp_state_dir)

    state.mark_failed("192.168.1.100", "web", "Connection timeout")

    deployment = state.get_deployment("192.168.1.100", "web")
    assert deployment is not None
    assert deployment["status"] == "failed"
    assert deployment["error"] == "Connection timeout"
    assert "failed_at" in deployment


def test_state_persistence(temp_state_dir):
    """Test that state persists across instances."""
    state1 = DeploymentState(temp_state_dir)
    state1.record_deployment(
        host="192.168.1.100",
        compose_file="docker-compose.yml",
        compose_hash="abc123",
    )

    state2 = DeploymentState(temp_state_dir)
    deployment = state2.get_deployment("192.168.1.100")
    assert deployment is not None
    assert deployment["compose_hash"] == "abc123"


def test_multiple_hosts(temp_state_dir):
    """Test tracking multiple hosts."""
    state = DeploymentState(temp_state_dir)

    state.record_deployment("192.168.1.100", "compose.yml", "hash1")
    state.record_deployment("192.168.1.101", "compose.yml", "hash2")

    assert state.get_deployment("192.168.1.100")["compose_hash"] == "hash1"
    assert state.get_deployment("192.168.1.101")["compose_hash"] == "hash2"


def test_multiple_services_per_host(temp_state_dir):
    """Test tracking multiple services on same host."""
    state = DeploymentState(temp_state_dir)

    state.record_deployment("192.168.1.100", "web.yml", "hash1", "web")
    state.record_deployment("192.168.1.100", "db.yml", "hash2", "db")

    assert state.get_deployment("192.168.1.100", "web")["compose_hash"] == "hash1"
    assert state.get_deployment("192.168.1.100", "db")["compose_hash"] == "hash2"
