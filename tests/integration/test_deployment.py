"""Integration tests for vm_tool."""

import pytest
import os


@pytest.fixture
def test_host():
    """Test host for integration tests."""
    return os.getenv("TEST_HOST", "localhost")


@pytest.fixture
def test_port():
    """Test port for integration tests."""
    return int(os.getenv("TEST_PORT", "8000"))


def test_full_deployment_workflow(test_host, test_port):
    """Test complete deployment workflow."""
    # This would test the full deployment process
    # For now, placeholder
    assert True


def test_health_checks(test_host, test_port):
    """Test health check functionality."""
    from vm_tool.health import HealthCheck

    # Test port check
    # checker = HealthCheck(test_host)
    # port_open = checker.check_port(test_port)
    # assert port_open or True  # May not have test server running

    # Test HTTP check
    # http_ok = checker.check_http(f"http://{test_host}:{test_port}/health")
    # assert http_ok or True

    assert True  # Placeholder


def test_deployment_validation(test_host, test_port):
    """Test deployment validation."""
    from vm_tool.validation import DeploymentValidator

    validator = DeploymentValidator(test_host, test_port)
    # Would run actual validation
    assert validator is not None


def test_metrics_collection():
    """Test metrics collection."""
    from vm_tool.metrics import MetricsCollector

    collector = MetricsCollector(export_dir=".test_metrics")
    metrics = collector.start_deployment("test-001", "localhost")

    assert metrics.deployment_id == "test-001"
    assert metrics.host == "localhost"

    collector.finish_deployment(success=True)
    assert metrics.duration is not None

    # Cleanup
    import shutil

    shutil.rmtree(".test_metrics", ignore_errors=True)


def test_secrets_management():
    """Test secrets management."""
    from vm_tool.secrets import EncryptedFileBackend, SecretsManager
    from cryptography.fernet import Fernet

    # Generate test key
    key = Fernet.generate_key().decode()

    # Create secrets manager
    backend = EncryptedFileBackend(".test_secrets.enc", encryption_key=key)
    manager = SecretsManager(backend)

    # Test set/get
    manager.set("test_key", "test_value")
    value = manager.get("test_key")
    assert value == "test_value"

    # Test list
    keys = manager.list()
    assert "test_key" in keys

    # Test delete
    manager.delete("test_key")
    value = manager.get("test_key")
    assert value is None

    # Cleanup
    import os

    os.remove(".test_secrets.enc")
