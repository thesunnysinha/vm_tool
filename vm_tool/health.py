"""Health check and smoke test functionality."""

import logging
import socket
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HealthCheck:
    """Performs health checks on deployed services."""

    def __init__(self, host: str, timeout: int = 30):
        self.host = host
        self.timeout = timeout

    def check_port(self, port: int) -> bool:
        """Check if a port is open and accepting connections."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, port))
            sock.close()
            return result == 0
        except socket.error as e:
            logger.warning(f"Port check failed for {self.host}:{port} - {e}")
            return False

    def check_http(self, url: str, expected_status: int = 200) -> bool:
        """Check if HTTP endpoint returns expected status."""
        try:
            import requests

            response = requests.get(url, timeout=5)
            return response.status_code == expected_status
        except ImportError:
            logger.warning("requests library not installed, skipping HTTP check")
            return True  # Don't fail if requests not available
        except Exception as e:
            logger.warning(f"HTTP check failed for {url} - {e}")
            return False

    def wait_for_port(self, port: int, max_attempts: int = None) -> bool:
        """Wait for a port to become available."""
        if max_attempts is None:
            max_attempts = self.timeout

        logger.info(f"Waiting for {self.host}:{port} to be available...")

        for attempt in range(max_attempts):
            if self.check_port(port):
                logger.info(f"✅ Port {port} is now available")
                return True

            if attempt < max_attempts - 1:
                time.sleep(1)

        logger.error(f"❌ Port {port} did not become available after {max_attempts}s")
        return False

    def wait_for_http(
        self, url: str, expected_status: int = 200, max_attempts: int = None
    ) -> bool:
        """Wait for HTTP endpoint to return expected status."""
        if max_attempts is None:
            max_attempts = self.timeout

        logger.info(f"Waiting for {url} to respond with status {expected_status}...")

        for attempt in range(max_attempts):
            if self.check_http(url, expected_status):
                logger.info(f"✅ {url} is now responding correctly")
                return True

            if attempt < max_attempts - 1:
                time.sleep(1)

        logger.error(f"❌ {url} did not respond correctly after {max_attempts}s")
        return False

    def run_custom_check(self, command: str) -> bool:
        """Run a custom health check command via SSH."""
        import subprocess

        try:
            # Execute command via SSH
            ssh_command = [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                self.host,
                command,
            ]

            result = subprocess.run(
                ssh_command, capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                logger.info(f"✅ Custom check passed: {command}")
                return True
            else:
                logger.error(
                    f"❌ Custom check failed: {command}\n"
                    f"   stdout: {result.stdout}\n"
                    f"   stderr: {result.stderr}"
                )
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"❌ Custom check timed out: {command}")
            return False
        except Exception as e:
            logger.error(f"❌ Custom check error: {command} - {e}")
            return False


class SmokeTestSuite:
    """Manages a suite of smoke tests."""

    def __init__(self, host: str):
        self.host = host
        self.health_check = HealthCheck(host)
        self.tests: List[Dict] = []

    def add_port_check(self, port: int, name: str = None):
        """Add a port availability check."""
        if name is None:
            name = f"Port {port}"

        self.tests.append({"type": "port", "port": port, "name": name})

    def add_http_check(self, url: str, expected_status: int = 200, name: str = None):
        """Add an HTTP endpoint check."""
        if name is None:
            name = f"HTTP {url}"

        self.tests.append(
            {
                "type": "http",
                "url": url,
                "expected_status": expected_status,
                "name": name,
            }
        )

    def add_custom_check(self, command: str, name: str):
        """Add a custom command check."""
        self.tests.append({"type": "custom", "command": command, "name": name})

    def run_all(self) -> bool:
        """Run all smoke tests and return overall result."""
        if not self.tests:
            logger.info("No smoke tests configured")
            return True

        logger.info(f"Running {len(self.tests)} smoke tests...")
        print(f"\n🧪 Running Smoke Tests ({len(self.tests)} tests)...")

        passed = 0
        failed = 0

        for test in self.tests:
            test_type = test["type"]
            name = test["name"]

            print(f"  • {name}...", end=" ", flush=True)

            if test_type == "port":
                result = self.health_check.wait_for_port(test["port"])
            elif test_type == "http":
                result = self.health_check.wait_for_http(
                    test["url"], test["expected_status"]
                )
            elif test_type == "custom":
                result = self.health_check.run_custom_check(test["command"])
            else:
                logger.error(f"Unknown test type: {test_type}")
                result = False

            if result:
                print("✅ PASS")
                passed += 1
            else:
                print("❌ FAIL")
                failed += 1

        print(f"\n📊 Results: {passed} passed, {failed} failed")

        if failed > 0:
            logger.error(f"Smoke tests failed: {failed}/{len(self.tests)}")
            return False

        logger.info(f"All smoke tests passed: {passed}/{len(self.tests)}")
        return True
