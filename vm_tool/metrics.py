"""Metrics collection and export for deployments."""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DeploymentMetrics:
    """Metrics for a deployment."""

    deployment_id: str
    host: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error: Optional[str] = None):
        """Mark deployment as finished."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "deployment_id": self.deployment_id,
            "host": self.host,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": (
                datetime.fromtimestamp(self.end_time).isoformat()
                if self.end_time
                else None
            ),
            "duration_seconds": self.duration,
            "success": self.success,
            "error": self.error,
            **self.metadata,
        }


class MetricsCollector:
    """Collect and export deployment metrics."""

    def __init__(self, export_dir: str = ".vm_tool/metrics"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.current_deployment: Optional[DeploymentMetrics] = None

    def start_deployment(
        self, deployment_id: str, host: str, **metadata
    ) -> DeploymentMetrics:
        """Start tracking a deployment."""
        self.current_deployment = DeploymentMetrics(
            deployment_id=deployment_id, host=host, metadata=metadata
        )
        logger.info(f"📊 Started tracking deployment: {deployment_id}")
        return self.current_deployment

    def finish_deployment(self, success: bool = True, error: Optional[str] = None):
        """Finish tracking current deployment."""
        if self.current_deployment:
            self.current_deployment.finish(success, error)
            self._export_metrics(self.current_deployment)
            logger.info(
                f"📊 Deployment metrics recorded: {self.current_deployment.duration:.2f}s"
            )

    def _export_metrics(self, metrics: DeploymentMetrics):
        """Export metrics to file."""
        import json

        # Export to JSON
        metrics_file = self.export_dir / f"{metrics.deployment_id}.json"
        with open(metrics_file, "w") as f:
            json.dump(metrics.to_dict(), f, indent=2)

        # Append to metrics log
        log_file = self.export_dir / "deployments.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(metrics.to_dict()) + "\n")

    def export_prometheus(
        self, metrics: DeploymentMetrics, output_file: str = "metrics.prom"
    ):
        """Export metrics in Prometheus format."""
        prom_file = self.export_dir / output_file

        with open(prom_file, "w") as f:
            # Deployment duration
            f.write(f"# HELP deployment_duration_seconds Time taken for deployment\n")
            f.write(f"# TYPE deployment_duration_seconds gauge\n")
            f.write(
                f'deployment_duration_seconds{{host="{metrics.host}",deployment_id="{metrics.deployment_id}"}} {metrics.duration or 0}\n\n'
            )

            # Deployment success
            f.write(
                f"# HELP deployment_success Whether deployment succeeded (1) or failed (0)\n"
            )
            f.write(f"# TYPE deployment_success gauge\n")
            f.write(
                f'deployment_success{{host="{metrics.host}",deployment_id="{metrics.deployment_id}"}} {1 if metrics.success else 0}\n\n'
            )

            # Deployment timestamp
            f.write(f"# HELP deployment_timestamp_seconds Deployment start time\n")
            f.write(f"# TYPE deployment_timestamp_seconds gauge\n")
            f.write(
                f'deployment_timestamp_seconds{{host="{metrics.host}",deployment_id="{metrics.deployment_id}"}} {metrics.start_time}\n'
            )

        logger.info(f"📊 Prometheus metrics exported to {prom_file}")

    def get_stats(self, limit: int = 100) -> Dict[str, Any]:
        """Get deployment statistics."""
        import json

        log_file = self.export_dir / "deployments.jsonl"
        if not log_file.exists():
            return {"total": 0, "success": 0, "failed": 0}

        deployments = []
        with open(log_file) as f:
            for line in f:
                deployments.append(json.loads(line))

        # Get recent deployments
        recent = deployments[-limit:]

        total = len(recent)
        success = sum(1 for d in recent if d.get("success"))
        failed = total - success

        durations = [d["duration_seconds"] for d in recent if d.get("duration_seconds")]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_deployments": total,
            "successful": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "average_duration_seconds": avg_duration,
            "recent_deployments": recent[-10:],  # Last 10
        }

    def print_stats(self):
        """Print deployment statistics."""
        stats = self.get_stats()

        print("\n📊 Deployment Statistics")
        print("=" * 50)
        print(f"Total Deployments: {stats['total_deployments']}")
        print(f"Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
        print(f"Failed: {stats['failed']}")
        print(f"Average Duration: {stats['average_duration_seconds']:.2f}s")
        print("\nRecent Deployments:")
        for d in stats["recent_deployments"]:
            status = "✅" if d["success"] else "❌"
            print(
                f"  {status} {d['deployment_id']} - {d['host']} - {d['duration_seconds']:.2f}s"
            )


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
