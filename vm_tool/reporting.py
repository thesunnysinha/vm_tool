"""Deployment reporting and analytics."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DeploymentReport:
    """Generate comprehensive deployment reports."""

    def __init__(self, report_dir: str = ".vm_tool/reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_deployment_report(
        self, deployment_id: str, host: str, duration: float, success: bool, **metadata
    ) -> Dict[str, Any]:
        """Generate report for a single deployment."""
        report = {
            "deployment_id": deployment_id,
            "host": host,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "success": success,
            "metadata": metadata,
        }

        # Save report
        report_file = self.report_dir / f"{deployment_id}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📊 Deployment report saved: {report_file}")

        return report

    def generate_summary_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate summary report for recent deployments."""
        logger.info(f"📊 Generating summary report for last {days} days")

        # Load recent deployments
        cutoff_date = datetime.now() - timedelta(days=days)
        deployments = []

        for report_file in self.report_dir.glob("*.json"):
            try:
                with open(report_file) as f:
                    deployment = json.load(f)

                    # Check if within date range
                    timestamp = datetime.fromisoformat(deployment.get("timestamp", ""))
                    if timestamp >= cutoff_date:
                        deployments.append(deployment)
            except Exception as e:
                logger.warning(f"Failed to load report {report_file}: {e}")

        # Calculate statistics
        total = len(deployments)
        successful = sum(1 for d in deployments if d.get("success"))
        failed = total - successful

        durations = [
            d["duration_seconds"] for d in deployments if "duration_seconds" in d
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Group by host
        hosts = {}
        for d in deployments:
            host = d.get("host", "unknown")
            if host not in hosts:
                hosts[host] = {"total": 0, "successful": 0, "failed": 0}
            hosts[host]["total"] += 1
            if d.get("success"):
                hosts[host]["successful"] += 1
            else:
                hosts[host]["failed"] += 1

        summary = {
            "period_days": days,
            "total_deployments": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "average_duration_seconds": avg_duration,
            "hosts": hosts,
            "recent_deployments": sorted(
                deployments, key=lambda x: x.get("timestamp", ""), reverse=True
            )[
                :10
            ],  # Last 10
        }

        # Save summary
        summary_file = (
            self.report_dir / f"summary_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"📊 Summary report saved: {summary_file}")

        return summary

    def print_summary_report(self, days: int = 7):
        """Print summary report to console."""
        summary = self.generate_summary_report(days)

        print(f"\n📊 Deployment Summary Report ({days} days)")
        print("=" * 60)
        print(f"Total Deployments: {summary['total_deployments']}")
        print(f"Successful: {summary['successful']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Average Duration: {summary['average_duration_seconds']:.2f}s")

        print("\nDeployments by Host:")
        for host, stats in summary["hosts"].items():
            success_rate = (
                (stats["successful"] / stats["total"] * 100)
                if stats["total"] > 0
                else 0
            )
            print(f"  {host}: {stats['total']} total, {success_rate:.1f}% success")

        print("\nRecent Deployments:")
        for d in summary["recent_deployments"]:
            status = "✅" if d["success"] else "❌"
            timestamp = datetime.fromisoformat(d["timestamp"]).strftime(
                "%Y-%m-%d %H:%M"
            )
            print(f"  {status} {d['deployment_id']} - {d['host']} - {timestamp}")

    def export_to_html(
        self, days: int = 7, output_file: str = "deployment_report.html"
    ):
        """Export report to HTML."""
        summary = self.generate_summary_report(days)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Deployment Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f5f5f5; padding: 15px; border-radius: 5px; flex: 1; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #007bff; color: white; }}
        .success {{ color: green; }}
        .failed {{ color: red; }}
    </style>
</head>
<body>
    <h1>Deployment Report ({days} days)</h1>
    
    <div class="stats">
        <div class="stat-card">
            <div>Total Deployments</div>
            <div class="stat-value">{summary['total_deployments']}</div>
        </div>
        <div class="stat-card">
            <div>Success Rate</div>
            <div class="stat-value">{summary['success_rate']:.1f}%</div>
        </div>
        <div class="stat-card">
            <div>Avg Duration</div>
            <div class="stat-value">{summary['average_duration_seconds']:.1f}s</div>
        </div>
    </div>
    
    <h2>Recent Deployments</h2>
    <table>
        <tr>
            <th>Status</th>
            <th>ID</th>
            <th>Host</th>
            <th>Timestamp</th>
            <th>Duration</th>
        </tr>
"""

        for d in summary["recent_deployments"]:
            status_class = "success" if d["success"] else "failed"
            status_icon = "✅" if d["success"] else "❌"
            timestamp = datetime.fromisoformat(d["timestamp"]).strftime(
                "%Y-%m-%d %H:%M"
            )

            html += f"""
        <tr>
            <td class="{status_class}">{status_icon}</td>
            <td>{d['deployment_id']}</td>
            <td>{d['host']}</td>
            <td>{timestamp}</td>
            <td>{d.get('duration_seconds', 0):.2f}s</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""

        output_path = self.report_dir / output_file
        with open(output_path, "w") as f:
            f.write(html)

        logger.info(f"📊 HTML report exported: {output_path}")
        return str(output_path)
