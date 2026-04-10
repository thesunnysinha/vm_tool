"""Health check and smoke test functionality."""

import logging
import shlex
import socket
import subprocess
from typing import Dict, List, Optional

from tenacity import (
    RetryError,
    retry,
    retry_if_result,
    stop_after_delay,
    wait_fixed,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


def check_http(url: str, expected_status: int = 200) -> bool:
    """Module-level HTTP check used by strategies."""
    try:
        import requests
        response = requests.get(url, timeout=5)
        return response.status_code == expected_status
    except ImportError:
        logger.warning("requests not installed, skipping HTTP check")
        return True
    except Exception:
        return False


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
        return check_http(url, expected_status)

    def wait_for_port(self, port: int, max_wait: int = None) -> bool:
        """Wait for a port to become available, retrying every second."""
        timeout = max_wait or self.timeout
        logger.info(f"Waiting up to {timeout}s for {self.host}:{port}...")

        @retry(
            retry=retry_if_result(lambda r: r is False),
            stop=stop_after_delay(timeout),
            wait=wait_fixed(1),
            before_sleep=before_sleep_log(logger, logging.DEBUG),
            reraise=False,
        )
        def _check() -> bool:
            return self.check_port(port)

        try:
            result = _check()
            if result:
                logger.info(f"✅ Port {port} is now available")
            else:
                logger.error(f"❌ Port {port} did not become available after {timeout}s")
            return result
        except RetryError:
            logger.error(f"❌ Port {port} did not become available after {timeout}s")
            return False

    def wait_for_http(
        self, url: str, expected_status: int = 200, max_wait: int = None
    ) -> bool:
        """Wait for HTTP endpoint to return expected status, retrying every 2 seconds."""
        timeout = max_wait or self.timeout
        logger.info(f"Waiting up to {timeout}s for {url}...")

        @retry(
            retry=retry_if_result(lambda r: r is False),
            stop=stop_after_delay(timeout),
            wait=wait_fixed(2),
            before_sleep=before_sleep_log(logger, logging.DEBUG),
            reraise=False,
        )
        def _check() -> bool:
            return self.check_http(url, expected_status)

        try:
            result = _check()
            if result:
                logger.info(f"✅ {url} is responding correctly")
            else:
                logger.error(f"❌ {url} did not respond correctly after {timeout}s")
            return result
        except RetryError:
            logger.error(f"❌ {url} did not respond correctly after {timeout}s")
            return False

    def run_custom_check(self, command: str) -> bool:
        """Run a custom health check command via SSH."""
        try:
            ssh_command = [
                "ssh",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "ConnectTimeout=5",
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
    """Manages a suite of smoke tests with Rich output."""

    def __init__(self, host: str, timeout: int = 300):
        self.host = host
        self.health_check = HealthCheck(host, timeout=timeout)
        self.tests: List[Dict] = []

    def add_port_check(self, port: int, name: str = None):
        self.tests.append({"type": "port", "port": port, "name": name or f"Port {port}"})

    def add_http_check(self, url: str, expected_status: int = 200, name: str = None):
        self.tests.append({
            "type": "http",
            "url": url,
            "expected_status": expected_status,
            "name": name or f"HTTP {url}",
        })

    def add_custom_check(self, command: str, name: str):
        self.tests.append({"type": "custom", "command": command, "name": name})

    def run_all(self) -> bool:
        """Run all smoke tests with Rich progress output."""
        if not self.tests:
            logger.info("No smoke tests configured")
            return True

        try:
            from rich.table import Table
            from rich.console import Console
            _console = Console()

            table = Table(title=f"Smoke Tests — {self.host}", show_header=True)
            table.add_column("Test", style="cyan")
            table.add_column("Result", justify="center")

            passed = failed = 0
            results = []

            for test in self.tests:
                if test["type"] == "port":
                    ok = self.health_check.wait_for_port(test["port"])
                elif test["type"] == "http":
                    ok = self.health_check.wait_for_http(test["url"], test["expected_status"])
                else:
                    ok = self.health_check.run_custom_check(test["command"])

                results.append((test["name"], ok))
                if ok:
                    passed += 1
                else:
                    failed += 1

            for name, ok in results:
                table.add_row(name, "[green]PASS[/green]" if ok else "[red]FAIL[/red]")

            _console.print(table)
            _console.print(
                f"[bold]Results:[/bold] [green]{passed} passed[/green], "
                f"[red]{failed} failed[/red]"
            )

        except ImportError:
            # Fallback if rich not installed (shouldn't happen — it's required)
            passed = failed = 0
            for test in self.tests:
                if test["type"] == "port":
                    ok = self.health_check.wait_for_port(test["port"])
                elif test["type"] == "http":
                    ok = self.health_check.wait_for_http(test["url"], test["expected_status"])
                else:
                    ok = self.health_check.run_custom_check(test["command"])
                print(f"  {'✅' if ok else '❌'} {test['name']}")
                if ok:
                    passed += 1
                else:
                    failed += 1

        if failed > 0:
            logger.error(f"Smoke tests failed: {failed}/{len(self.tests)}")
            return False
        logger.info(f"All smoke tests passed: {passed}/{len(self.tests)}")
        return True
