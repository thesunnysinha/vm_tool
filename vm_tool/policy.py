"""Policy as Code framework for deployment policies."""

import logging
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PolicyViolation:
    """Policy violation details."""

    policy_name: str
    message: str
    severity: str  # "error", "warning", "info"


class Policy:
    """Base policy class."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def evaluate(self, context: Dict[str, Any]) -> List[PolicyViolation]:
        """Evaluate policy against context."""
        raise NotImplementedError


class DeploymentPolicy(Policy):
    """Policy for deployment validation."""

    def __init__(self, name: str, description: str, rules: List[Callable]):
        super().__init__(name, description)
        self.rules = rules

    def evaluate(self, context: Dict[str, Any]) -> List[PolicyViolation]:
        """Evaluate all rules."""
        violations = []

        for rule in self.rules:
            try:
                violation = rule(context)
                if violation:
                    violations.append(violation)
            except Exception as e:
                logger.error(f"Policy rule failed: {e}")

        return violations


class PolicyEngine:
    """Policy evaluation engine."""

    def __init__(self):
        self.policies: List[Policy] = []
        self._register_default_policies()

    def _register_default_policies(self):
        """Register default policies."""
        # Production deployment policy
        self.add_policy(
            DeploymentPolicy(
                name="production_safety",
                description="Safety checks for production deployments",
                rules=[
                    self._require_approval_for_production,
                    self._require_backup_before_deploy,
                    self._require_health_checks,
                ],
            )
        )

        # Security policy
        self.add_policy(
            DeploymentPolicy(
                name="security",
                description="Security requirements",
                rules=[
                    self._require_secrets_encryption,
                    self._no_hardcoded_credentials,
                ],
            )
        )

    def add_policy(self, policy: Policy):
        """Add a policy."""
        self.policies.append(policy)
        logger.info(f"Policy registered: {policy.name}")

    def evaluate_all(self, context: Dict[str, Any]) -> List[PolicyViolation]:
        """Evaluate all policies."""
        all_violations = []

        for policy in self.policies:
            violations = policy.evaluate(context)
            all_violations.extend(violations)

        return all_violations

    def enforce(self, context: Dict[str, Any]) -> bool:
        """Enforce policies (fail on errors)."""
        violations = self.evaluate_all(context)

        errors = [v for v in violations if v.severity == "error"]
        warnings = [v for v in violations if v.severity == "warning"]

        if warnings:
            for v in warnings:
                logger.warning(f"Policy warning [{v.policy_name}]: {v.message}")

        if errors:
            for v in errors:
                logger.error(f"Policy violation [{v.policy_name}]: {v.message}")
            return False

        return True

    # Default policy rules
    def _require_approval_for_production(
        self, context: Dict[str, Any]
    ) -> Optional[PolicyViolation]:
        """Require manual approval for production."""
        if context.get("environment") == "production" and not context.get("approved"):
            return PolicyViolation(
                policy_name="production_safety",
                message="Production deployments require manual approval",
                severity="error",
            )
        return None

    def _require_backup_before_deploy(
        self, context: Dict[str, Any]
    ) -> Optional[PolicyViolation]:
        """Require backup before deployment."""
        if context.get("environment") == "production" and not context.get(
            "backup_created"
        ):
            return PolicyViolation(
                policy_name="production_safety",
                message="Backup required before production deployment",
                severity="warning",
            )
        return None

    def _require_health_checks(
        self, context: Dict[str, Any]
    ) -> Optional[PolicyViolation]:
        """Require health checks."""
        if not context.get("health_checks_enabled"):
            return PolicyViolation(
                policy_name="production_safety",
                message="Health checks must be enabled",
                severity="warning",
            )
        return None

    def _require_secrets_encryption(
        self, context: Dict[str, Any]
    ) -> Optional[PolicyViolation]:
        """Require encrypted secrets."""
        if context.get("secrets_plaintext"):
            return PolicyViolation(
                policy_name="security",
                message="Secrets must be encrypted",
                severity="error",
            )
        return None

    def _no_hardcoded_credentials(
        self, context: Dict[str, Any]
    ) -> Optional[PolicyViolation]:
        """Check for hardcoded credentials."""
        compose_content = context.get("compose_file_content", "")
        if (
            "password:" in compose_content.lower()
            or "secret:" in compose_content.lower()
        ):
            return PolicyViolation(
                policy_name="security",
                message="Possible hardcoded credentials detected",
                severity="warning",
            )
        return None


# Global policy engine
_policy_engine = None


def get_policy_engine() -> PolicyEngine:
    """Get global policy engine instance."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
