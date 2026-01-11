"""Deployment validation framework."""

import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation check status."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class ValidationResult:
    """Result of a validation check."""

    name: str
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None


class DeploymentValidator:
    """Validate deployment readiness and health."""

    def __init__(self, host: str, port: int = 8000):
        self.host = host
        self.port = port
        self.checks: List[Callable] = []
        self.results: List[ValidationResult] = []

    def add_check(self, check_func: Callable, name: str):
        """Add a validation check."""
        self.checks.append((name, check_func))

    def validate_all(self) -> bool:
        """Run all validation checks.

        Returns:
            True if all checks passed, False otherwise
        """
        self.results = []
        all_passed = True

        logger.info(f"🔍 Running {len(self.checks)} validation checks...")

        for name, check_func in self.checks:
            try:
                result = check_func()
                self.results.append(result)

                if result.status == ValidationStatus.PASSED:
                    logger.info(f"  ✅ {name}: {result.message}")
                elif result.status == ValidationStatus.WARNING:
                    logger.warning(f"  ⚠️  {name}: {result.message}")
                elif result.status == ValidationStatus.FAILED:
                    logger.error(f"  ❌ {name}: {result.message}")
                    all_passed = False
                else:  # SKIPPED
                    logger.info(f"  ⏭️  {name}: {result.message}")

            except Exception as e:
                logger.error(f"  ❌ {name}: Check failed with error: {e}")
                self.results.append(
                    ValidationResult(
                        name=name,
                        status=ValidationStatus.FAILED,
                        message=f"Check failed: {e}",
                    )
                )
                all_passed = False

        return all_passed

    def check_port_open(self) -> ValidationResult:
        """Check if application port is open."""
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()

            if result == 0:
                return ValidationResult(
                    name="Port Check",
                    status=ValidationStatus.PASSED,
                    message=f"Port {self.port} is open",
                )
            else:
                return ValidationResult(
                    name="Port Check",
                    status=ValidationStatus.FAILED,
                    message=f"Port {self.port} is not accessible",
                )
        except Exception as e:
            return ValidationResult(
                name="Port Check",
                status=ValidationStatus.FAILED,
                message=f"Port check failed: {e}",
            )

    def check_http_response(self, endpoint: str = "/") -> ValidationResult:
        """Check if HTTP endpoint responds."""
        import requests

        url = f"http://{self.host}:{self.port}{endpoint}"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return ValidationResult(
                    name="HTTP Response",
                    status=ValidationStatus.PASSED,
                    message=f"Endpoint {endpoint} returned 200",
                    details={"status_code": response.status_code},
                )
            else:
                return ValidationResult(
                    name="HTTP Response",
                    status=ValidationStatus.WARNING,
                    message=f"Endpoint {endpoint} returned {response.status_code}",
                    details={"status_code": response.status_code},
                )
        except Exception as e:
            return ValidationResult(
                name="HTTP Response",
                status=ValidationStatus.FAILED,
                message=f"HTTP check failed: {e}",
            )

    def check_health_endpoint(self, endpoint: str = "/health") -> ValidationResult:
        """Check health endpoint."""
        import requests

        url = f"http://{self.host}:{self.port}{endpoint}"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    status = data.get("status", "unknown")

                    if status == "healthy" or status == "ok":
                        return ValidationResult(
                            name="Health Check",
                            status=ValidationStatus.PASSED,
                            message="Application is healthy",
                            details=data,
                        )
                    else:
                        return ValidationResult(
                            name="Health Check",
                            status=ValidationStatus.WARNING,
                            message=f"Health status: {status}",
                            details=data,
                        )
                except:
                    return ValidationResult(
                        name="Health Check",
                        status=ValidationStatus.PASSED,
                        message="Health endpoint accessible",
                    )
            else:
                return ValidationResult(
                    name="Health Check",
                    status=ValidationStatus.FAILED,
                    message=f"Health endpoint returned {response.status_code}",
                )
        except Exception as e:
            return ValidationResult(
                name="Health Check",
                status=ValidationStatus.FAILED,
                message=f"Health check failed: {e}",
            )

    def check_database_connection(self, db_url: str) -> ValidationResult:
        """Check database connectivity."""
        # Placeholder - would implement actual DB connection check
        return ValidationResult(
            name="Database Connection",
            status=ValidationStatus.SKIPPED,
            message="Database check not configured",
        )

    def check_dependencies(self, dependencies: List[str]) -> ValidationResult:
        """Check if required dependencies are available."""
        # Placeholder - would check service dependencies
        return ValidationResult(
            name="Dependencies Check",
            status=ValidationStatus.SKIPPED,
            message="Dependency check not configured",
        )

    def generate_report(self) -> str:
        """Generate validation report."""
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == ValidationStatus.SKIPPED)

        report = f"""
Deployment Validation Report
============================
Host: {self.host}:{self.port}
Total Checks: {len(self.results)}

Results:
  ✅ Passed:  {passed}
  ❌ Failed:  {failed}
  ⚠️  Warnings: {warnings}
  ⏭️  Skipped: {skipped}

Details:
"""
        for result in self.results:
            icon = {
                ValidationStatus.PASSED: "✅",
                ValidationStatus.FAILED: "❌",
                ValidationStatus.WARNING: "⚠️",
                ValidationStatus.SKIPPED: "⏭️",
            }[result.status]

            report += f"\n{icon} {result.name}: {result.message}"
            if result.details:
                report += f"\n   Details: {result.details}"

        return report


def validate_deployment(host: str, port: int = 8000) -> bool:
    """Quick deployment validation.

    Args:
        host: Host to validate
        port: Port to check

    Returns:
        True if validation passed, False otherwise
    """
    validator = DeploymentValidator(host, port)

    # Add standard checks
    validator.add_check(validator.check_port_open, "Port Accessibility")
    validator.add_check(validator.check_http_response, "HTTP Response")
    validator.add_check(
        lambda: validator.check_health_endpoint("/health"), "Health Endpoint"
    )

    # Run validation
    result = validator.validate_all()

    # Print report
    print(validator.generate_report())

    return result
