"""A/B testing and traffic splitting strategies."""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VariantType(Enum):
    """A/B test variant type."""

    CONTROL = "control"  # Original version
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


@dataclass
class Variant:
    """A/B test variant configuration."""

    name: str
    host: str
    traffic_percentage: float
    description: Optional[str] = None


class ABTestDeployment:
    """Manage A/B testing deployments."""

    def __init__(self, variants: List[Variant], ssh_user: Optional[str] = None):
        """Initialize A/B test deployment.

        Args:
            variants: List of test variants
            ssh_user: SSH user for connecting to variant hosts
        """
        self.variants = variants
        self.ssh_user = ssh_user
        self._validate_traffic_percentages()

    def _validate_traffic_percentages(self):
        """Validate that traffic percentages sum to 100."""
        total = sum(v.traffic_percentage for v in self.variants)
        if abs(total - 100.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Traffic percentages must sum to 100%, got {total}%")

    def deploy(self, compose_files: Dict[str, str]) -> Dict[str, Any]:
        """Deploy A/B test variants.

        Args:
            compose_files: Mapping of variant name to compose file

        Returns:
            Deployment result
        """
        logger.info("🧪 Starting A/B test deployment")
        logger.info(f"   Variants: {len(self.variants)}")

        result = {
            "success": False,
            "deployed_variants": [],
            "failed_variants": [],
        }

        # Deploy each variant
        for variant in self.variants:
            logger.info(
                f"📦 Deploying variant '{variant.name}' ({variant.traffic_percentage}%)"
            )
            logger.info(f"   Host: {variant.host}")

            compose_file = compose_files.get(variant.name)
            if not compose_file:
                logger.warning(
                    f"   ⚠️  No compose file for variant '{variant.name}', skipping"
                )
                continue

            try:
                self._deploy_variant(variant, compose_file)
                result["deployed_variants"].append(variant.name)
                logger.info(f"   ✅ Variant '{variant.name}' deployed")
            except Exception as e:
                logger.error(f"   ❌ Variant '{variant.name}' failed: {e}")
                result["failed_variants"].append(variant.name)

        # Configure traffic splitting
        if not result["failed_variants"]:
            logger.info("🔄 Configuring traffic splitting...")
            self._configure_traffic_split()
            result["success"] = True

        return result

    def _deploy_variant(self, variant: Variant, compose_file: str):
        """Deploy a single variant to its host using Docker Compose."""
        from vm_tool.core.runner import SetupRunner, SetupRunnerConfig
        SetupRunner(SetupRunnerConfig()).run_docker_deploy(
            compose_file=compose_file,
            host=variant.host,
            user=self.ssh_user,
            force=True,
        )

    def _configure_traffic_split(self):
        """Configure load balancer for traffic splitting.

        Override this method for your load balancer.
        See docs/strategies.md for nginx, AWS ALB, and HAProxy examples.
        """
        weights = {v.name: v.traffic_percentage for v in self.variants}
        raise NotImplementedError(
            f"_configure_traffic_split must be overridden for your load balancer. "
            f"Weights: {weights}. "
            f"See docs/strategies.md for nginx, AWS ALB, and HAProxy examples."
        )

    def get_variant_metrics(self, variant_name: str) -> Dict[str, Any]:
        """Get metrics for a specific variant.

        Args:
            variant_name: Name of the variant

        Returns:
            Variant metrics
        """
        # This would fetch actual metrics from monitoring system
        return {
            "variant": variant_name,
            "requests": 1000,
            "success_rate": 99.5,
            "avg_response_time": 120,
            "conversion_rate": 5.2,
        }

    def compare_variants(self) -> Dict[str, Any]:
        """Compare metrics across all variants.

        Returns:
            Comparison results
        """
        logger.info("📊 Comparing variant metrics...")

        comparison = {
            "variants": {},
            "winner": None,
        }

        best_conversion = 0
        best_variant = None

        for variant in self.variants:
            metrics = self.get_variant_metrics(variant.name)
            comparison["variants"][variant.name] = metrics

            conversion = metrics.get("conversion_rate", 0)
            if conversion > best_conversion:
                best_conversion = conversion
                best_variant = variant.name

        comparison["winner"] = best_variant

        logger.info(f"   Winner: {best_variant} ({best_conversion}% conversion)")

        return comparison

    def promote_winner(self, winner_name: str) -> bool:
        """Promote winning variant to 100% traffic.

        Args:
            winner_name: Name of winning variant

        Returns:
            True if promotion successful
        """
        logger.info(f"🏆 Promoting variant '{winner_name}' to 100% traffic")

        # Update traffic percentages
        for variant in self.variants:
            if variant.name == winner_name:
                variant.traffic_percentage = 100.0
            else:
                variant.traffic_percentage = 0.0

        # Reconfigure traffic split
        self._configure_traffic_split()

        logger.info("✅ Winner promoted successfully")
        return True


class TrafficSplitter:
    """Manage traffic splitting across multiple backends."""

    def __init__(self, backends: Dict[str, str]):
        """Initialize traffic splitter.

        Args:
            backends: Mapping of backend name to host
        """
        self.backends = backends
        self.traffic_weights: Dict[str, float] = {}

    def set_weights(self, weights: Dict[str, float]):
        """Set traffic weights for backends.

        Args:
            weights: Mapping of backend name to weight (0-100)
        """
        total = sum(weights.values())
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Weights must sum to 100%, got {total}%")

        self.traffic_weights = weights
        self._apply_weights()

    def _apply_weights(self):
        """Apply traffic weights to load balancer.

        Override this method for your load balancer.
        See docs/strategies.md for nginx, AWS ALB, and HAProxy examples.
        """
        logger.info("🔄 Applying traffic weights:")
        for backend, weight in self.traffic_weights.items():
            logger.info(f"   {backend}: {weight}%")
        raise NotImplementedError(
            f"_apply_weights must be overridden for your load balancer. "
            f"Weights: {self.traffic_weights}. "
            f"See docs/strategies.md for nginx, AWS ALB, and HAProxy examples."
        )

    def gradual_shift(
        self,
        from_backend: str,
        to_backend: str,
        increment: float = 10.0,
        interval: int = 60,
    ):
        """Gradually shift traffic from one backend to another.

        Args:
            from_backend: Source backend
            to_backend: Target backend
            increment: Percentage to shift per step
            interval: Seconds between shifts
        """
        logger.info(f"🔄 Gradual traffic shift: {from_backend} → {to_backend}")

        current_from = self.traffic_weights.get(from_backend, 100.0)
        current_to = self.traffic_weights.get(to_backend, 0.0)

        import time

        while current_from > 0:
            shift_amount = min(increment, current_from)
            current_from -= shift_amount
            current_to += shift_amount

            self.traffic_weights[from_backend] = current_from
            self.traffic_weights[to_backend] = current_to

            self._apply_weights()

            if current_from > 0:
                logger.info(f"   Waiting {interval}s before next shift...")
                time.sleep(interval)

        logger.info("✅ Traffic shift complete")
