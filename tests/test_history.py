"""Tests for deployment history and rollback."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vm_tool.history import DeploymentHistory


@pytest.fixture
def temp_history_dir(tmp_path):
    """Create a temporary history directory."""
    return tmp_path / ".vm_tool"


def test_record_deployment(temp_history_dir):
    """Test recording a deployment."""
    history = DeploymentHistory(temp_history_dir)

    deployment_id = history.record_deployment(
        host="192.168.1.100",
        compose_file="docker-compose.yml",
        compose_hash="abc123",
        git_commit="def456",
        service_name="web",
        status="success",
    )

    assert deployment_id is not None
    assert len(deployment_id) > 0


def test_get_history(temp_history_dir):
    """Test retrieving deployment history."""
    history = DeploymentHistory(temp_history_dir)

    # Record multiple deployments
    history.record_deployment("192.168.1.100", "compose.yml", "hash1")
    history.record_deployment("192.168.1.101", "compose.yml", "hash2")
    history.record_deployment("192.168.1.100", "compose.yml", "hash3")

    # Get all history
    all_history = history.get_history(limit=10)
    assert len(all_history) == 3

    # Get history for specific host
    host_history = history.get_history(host="192.168.1.100", limit=10)
    assert len(host_history) == 2


def test_get_deployment_by_id(temp_history_dir):
    """Test retrieving a specific deployment by ID."""
    history = DeploymentHistory(temp_history_dir)

    deployment_id = history.record_deployment(
        host="192.168.1.100",
        compose_file="docker-compose.yml",
        compose_hash="abc123",
    )

    deployment = history.get_deployment(deployment_id)
    assert deployment is not None
    assert deployment["id"] == deployment_id
    assert deployment["host"] == "192.168.1.100"


def test_get_previous_deployment(temp_history_dir):
    """Test getting the previous deployment."""
    history = DeploymentHistory(temp_history_dir)

    # Record first deployment
    id1 = history.record_deployment(
        host="192.168.1.100",
        compose_file="compose.yml",
        compose_hash="hash1",
        service_name="web",
        status="success",
    )

    # Record second deployment
    id2 = history.record_deployment(
        host="192.168.1.100",
        compose_file="compose.yml",
        compose_hash="hash2",
        service_name="web",
        status="success",
    )

    # Get previous deployment (should be id1)
    previous = history.get_previous_deployment("192.168.1.100", "web")
    assert previous is not None
    assert previous["id"] == id1


def test_get_previous_deployment_no_history(temp_history_dir):
    """Test getting previous deployment when there's no history."""
    history = DeploymentHistory(temp_history_dir)

    previous = history.get_previous_deployment("192.168.1.100")
    assert previous is None


def test_get_previous_deployment_only_one(temp_history_dir):
    """Test getting previous deployment when there's only one deployment."""
    history = DeploymentHistory(temp_history_dir)

    history.record_deployment(
        host="192.168.1.100",
        compose_file="compose.yml",
        compose_hash="hash1",
        status="success",
    )

    previous = history.get_previous_deployment("192.168.1.100")
    assert previous is None  # Need at least 2 deployments


def test_history_limit(temp_history_dir):
    """Test that history is limited to 100 entries."""
    history = DeploymentHistory(temp_history_dir)

    # Record 150 deployments
    for i in range(150):
        history.record_deployment(
            host="192.168.1.100",
            compose_file="compose.yml",
            compose_hash=f"hash{i}",
        )

    all_history = history.get_history(limit=200)
    assert len(all_history) == 100  # Should be capped at 100


def test_history_persistence(temp_history_dir):
    """Test that history persists across instances."""
    history1 = DeploymentHistory(temp_history_dir)
    deployment_id = history1.record_deployment(
        host="192.168.1.100",
        compose_file="compose.yml",
        compose_hash="abc123",
    )

    history2 = DeploymentHistory(temp_history_dir)
    deployment = history2.get_deployment(deployment_id)
    assert deployment is not None
    assert deployment["id"] == deployment_id


def test_get_rollback_info_by_id(temp_history_dir):
    """Test getting rollback info by deployment ID."""
    history = DeploymentHistory(temp_history_dir)

    deployment_id = history.record_deployment(
        host="192.168.1.100",
        compose_file="compose.yml",
        compose_hash="abc123",
        status="success",
    )

    rollback_info = history.get_rollback_info("192.168.1.100", deployment_id)
    assert rollback_info is not None
    assert rollback_info["id"] == deployment_id


def test_get_rollback_info_previous(temp_history_dir):
    """Test getting rollback info for previous deployment."""
    history = DeploymentHistory(temp_history_dir)

    id1 = history.record_deployment(
        host="192.168.1.100",
        compose_file="compose.yml",
        compose_hash="hash1",
        status="success",
    )

    history.record_deployment(
        host="192.168.1.100",
        compose_file="compose.yml",
        compose_hash="hash2",
        status="success",
    )

    rollback_info = history.get_rollback_info("192.168.1.100")
    assert rollback_info is not None
    assert rollback_info["id"] == id1
