"""Tests for health checks and smoke tests."""

import socket
from unittest.mock import MagicMock, patch

import pytest

from vm_tool.health import HealthCheck, SmokeTestSuite


def test_check_port_open():
    """Test checking an open port."""
    # Create a temporary server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))  # Bind to any available port
    server.listen(1)
    port = server.getsockname()[1]

    health = HealthCheck("127.0.0.1")
    assert health.check_port(port) is True

    server.close()


def test_check_port_closed():
    """Test checking a closed port."""
    health = HealthCheck("127.0.0.1")
    # Port 1 is typically not open
    assert health.check_port(1) is False


@patch("requests.get")
def test_check_http_success(mock_get):
    """Test successful HTTP check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    health = HealthCheck("example.com")
    assert health.check_http("http://example.com/health") is True


@patch("requests.get")
def test_check_http_failure(mock_get):
    """Test failed HTTP check."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    health = HealthCheck("example.com")
    assert health.check_http("http://example.com/health") is False


@patch("requests.get")
def test_check_http_custom_status(mock_get):
    """Test HTTP check with custom expected status."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    health = HealthCheck("example.com")
    assert health.check_http("http://example.com/notfound", expected_status=404) is True


def test_wait_for_port_immediate():
    """Test waiting for a port that's immediately available."""
    # Create a server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    health = HealthCheck("127.0.0.1", timeout=5)
    assert health.wait_for_port(port, max_attempts=3) is True

    server.close()


def test_wait_for_port_timeout():
    """Test waiting for a port that never becomes available."""
    health = HealthCheck("127.0.0.1", timeout=2)
    assert health.wait_for_port(1, max_attempts=2) is False


@patch("subprocess.run")
def test_run_custom_check_success(mock_run):
    """Test successful custom check."""
    mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

    health = HealthCheck("example.com")
    assert health.run_custom_check("echo OK") is True


@patch("subprocess.run")
def test_run_custom_check_failure(mock_run):
    """Test failed custom check."""
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

    health = HealthCheck("example.com")
    assert health.run_custom_check("false") is False


def test_smoke_test_suite_add_tests():
    """Test adding tests to smoke test suite."""
    suite = SmokeTestSuite("example.com")

    suite.add_port_check(8000)
    suite.add_http_check("http://example.com/health")
    suite.add_custom_check("echo OK", "Echo Test")

    assert len(suite.tests) == 3
    assert suite.tests[0]["type"] == "port"
    assert suite.tests[1]["type"] == "http"
    assert suite.tests[2]["type"] == "custom"


@patch.object(HealthCheck, "wait_for_port")
@patch.object(HealthCheck, "wait_for_http")
def test_smoke_test_suite_run_all_pass(mock_http, mock_port):
    """Test running all smoke tests with all passing."""
    mock_port.return_value = True
    mock_http.return_value = True

    suite = SmokeTestSuite("example.com")
    suite.add_port_check(8000)
    suite.add_http_check("http://example.com/health")

    assert suite.run_all() is True


@patch.object(HealthCheck, "wait_for_port")
@patch.object(HealthCheck, "wait_for_http")
def test_smoke_test_suite_run_all_fail(mock_http, mock_port):
    """Test running all smoke tests with one failing."""
    mock_port.return_value = True
    mock_http.return_value = False

    suite = SmokeTestSuite("example.com")
    suite.add_port_check(8000)
    suite.add_http_check("http://example.com/health")

    assert suite.run_all() is False


def test_smoke_test_suite_empty():
    """Test running empty smoke test suite."""
    suite = SmokeTestSuite("example.com")
    assert suite.run_all() is True  # Empty suite should pass
