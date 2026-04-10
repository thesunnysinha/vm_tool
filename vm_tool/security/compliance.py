"""Compliance scanning and security checks.

ComplianceScanner performs static analysis — no network, no external process.
CostOptimizer and DisasterRecovery require external metrics/infrastructure
and remain as overrideable stubs.
"""

import logging
import re
from typing import Any, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComplianceIssue:
    """A single compliance finding."""

    severity: str  # "critical", "high", "medium", "low"
    category: str
    description: str
    remediation: str


class ComplianceScanner:
    """Scan deployments for compliance and security issues.

    Example::

        scanner = ComplianceScanner()

        # Scan a docker-compose file
        issues = scanner.scan_docker_compose("docker-compose.yml")
        print(scanner.generate_compliance_report())

        # Scan a secrets dict
        issues = scanner.scan_secrets({"DB_PASSWORD": "hunter2"})
    """

    def __init__(self):
        self.issues: List[ComplianceIssue] = []

    def scan_docker_compose(self, compose_file: str) -> List[ComplianceIssue]:
        """Scan a docker-compose YAML file for security issues.

        Checks performed:
        - Services running as root (no user: directive or user: root/0)
        - privileged: true mode
        - Missing resource limits (deploy.resources.limits)
        - Ports bound to all interfaces (0.0.0.0)

        Args:
            compose_file: Path to docker-compose.yml

        Returns:
            List of ComplianceIssue found.
        """
        import yaml

        self.issues = []
        with open(compose_file) as f:
            data = yaml.safe_load(f)

        services = data.get("services", {}) if data else {}
        for svc_name, svc in services.items():
            if not isinstance(svc, dict):
                continue

            # Check: container running as root
            user = str(svc.get("user", "root"))
            if user in ("root", "0", "0:0", ""):
                self.issues.append(ComplianceIssue(
                    severity="high",
                    category="container-security",
                    description=f"Service '{svc_name}' runs as root (user: {user!r})",
                    remediation="Add 'user: 1000:1000' to the service definition",
                ))

            # Check: privileged mode
            if svc.get("privileged", False):
                self.issues.append(ComplianceIssue(
                    severity="critical",
                    category="container-security",
                    description=f"Service '{svc_name}' uses privileged mode",
                    remediation="Remove 'privileged: true' unless strictly necessary",
                ))

            # Check: no resource limits
            deploy = svc.get("deploy", {}) or {}
            if not deploy.get("resources", {}).get("limits"):
                self.issues.append(ComplianceIssue(
                    severity="medium",
                    category="resource-limits",
                    description=f"Service '{svc_name}' has no resource limits",
                    remediation=(
                        "Add deploy.resources.limits.memory and "
                        "deploy.resources.limits.cpus"
                    ),
                ))

            # Check: ports exposed on all interfaces
            for port in svc.get("ports", []):
                port_str = str(port)
                # Matches "0.0.0.0:8080:8080" or "8080:8080" (bare port binds to all)
                if "0.0.0.0" in port_str or (
                    ":" in port_str
                    and not port_str.startswith("127.")
                    and not port_str.startswith("localhost:")
                    and not port_str.startswith("::1")
                ):
                    self.issues.append(ComplianceIssue(
                        severity="low",
                        category="network-exposure",
                        description=(
                            f"Service '{svc_name}' port {port_str} "
                            f"is bound to all interfaces"
                        ),
                        remediation=(
                            "Bind to 127.0.0.1 unless public access is required: "
                            f"'127.0.0.1:{port_str}'"
                        ),
                    ))

        logger.info(
            f"Docker Compose scan complete: {len(self.issues)} issue(s) found in {compose_file}"
        )
        return self.issues

    def scan_secrets(self, secrets_config: Dict[str, Any]) -> List[ComplianceIssue]:
        """Scan a flat key-value dict for plaintext secrets.

        Flags keys that look like credential fields whose values do NOT look like
        template placeholders (${...}, {{...}}, <...>, todo, changeme, example).

        Args:
            secrets_config: Flat dict of env-var-like key/value pairs.

        Returns:
            List of ComplianceIssue found.
        """
        self.issues = []

        credential_patterns = [
            (r"(?i)password", "password"),
            (r"(?i)secret", "secret"),
            (r"(?i)api[_-]?key", "API key"),
            (r"(?i)token", "token"),
            (r"(?i)private[_-]?key", "private key"),
            (r"(?i)access[_-]?key", "access key"),
        ]
        # Values that look like placeholders — skip these
        placeholder_re = re.compile(
            r"^\$\{|^\$[A-Z_]|^\{\{|^<[^>]+>|^your[-_]|"
            r"^changeme$|^todo$|^example|^xxx|^replace|^none$",
            re.IGNORECASE,
        )

        for key, value in secrets_config.items():
            if not isinstance(value, str) or not value:
                continue
            if placeholder_re.match(value):
                continue
            for pattern, label in credential_patterns:
                if re.search(pattern, key):
                    self.issues.append(ComplianceIssue(
                        severity="high",
                        category="secrets-exposure",
                        description=(
                            f"Key '{key}' appears to contain a plaintext {label}"
                        ),
                        remediation=(
                            f"Move '{key}' to an encrypted secrets store "
                            f"(e.g. vm_tool secrets sync, HashiCorp Vault, or AWS Secrets Manager)"
                        ),
                    ))
                    break  # one issue per key

        logger.info(f"Secrets scan complete: {len(self.issues)} issue(s) found")
        return self.issues

    def generate_compliance_report(self) -> str:
        """Generate a human-readable compliance report from self.issues."""
        if not self.issues:
            return "✅ No compliance issues found"

        # Group by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(
            self.issues, key=lambda i: severity_order.get(i.severity, 99)
        )

        counts = {s: 0 for s in severity_order}
        for issue in self.issues:
            counts[issue.severity] = counts.get(issue.severity, 0) + 1

        report = f"Compliance Scan Report\n{'=' * 50}\n"
        report += f"Total Issues: {len(self.issues)}"
        parts = [f"{v} {k}" for k, v in counts.items() if v > 0]
        report += f" ({', '.join(parts)})\n\n"

        for issue in sorted_issues:
            report += f"[{issue.severity.upper()}] {issue.category}\n"
            report += f"  {issue.description}\n"
            report += f"  Remediation: {issue.remediation}\n\n"

        return report


class CostOptimizer:
    """Cost optimization recommendations.

    analyze_resource_usage() requires live metrics from your infrastructure
    (CPU/memory utilization, request rates, etc.). Override this method with
    your own metrics source (CloudWatch, Prometheus, etc.).
    """

    def analyze_resource_usage(self, metrics: Dict[str, Any]) -> List[str]:
        """Analyze resource usage and return optimization recommendations.

        Not implemented: requires live metrics from your infrastructure.
        Override this method and provide metrics from CloudWatch, Prometheus,
        or another source.

        Args:
            metrics: Dict of service_name → usage metrics.
        """
        raise NotImplementedError(
            "Cost optimization requires live infrastructure metrics. "
            "Override analyze_resource_usage() with your metrics source "
            "(e.g. CloudWatch, Prometheus query results)."
        )


class DisasterRecovery:
    """Disaster recovery automation.

    These methods require knowledge of your specific infrastructure topology
    (databases, object storage, DNS, load balancers). They cannot be implemented
    generically. Override them for your environment.
    """

    def create_dr_plan(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a disaster recovery plan.

        Not implemented: requires knowledge of your infrastructure topology.
        Override this method with your specific DR procedures.
        """
        raise NotImplementedError(
            "DR plan creation requires infrastructure-specific knowledge. "
            "Override create_dr_plan() with your environment's DR procedures."
        )

    def execute_failover(self, primary_region: str, dr_region: str) -> bool:
        """Execute failover to DR region.

        Not implemented: requires live infrastructure access and validated DR runbook.
        Override this method with your specific failover steps.
        """
        raise NotImplementedError(
            "Failover execution is environment-specific. "
            "Override execute_failover() with your validated DR runbook."
        )
