"""Performance benchmarking for deployments."""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from statistics import mean, median, stdev

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    name: str
    duration: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceBenchmark:
    """Benchmark deployment performance."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def benchmark_deployment(self, host: str, compose_file: str) -> BenchmarkResult:
        """Benchmark a deployment."""
        logger.info(f"🏃 Benchmarking deployment to {host}")

        start_time = time.time()
        success = False
        error = None

        try:
            # Simulate deployment (would call actual deploy function)
            logger.info("   Running deployment...")
            time.sleep(0.1)  # Placeholder
            success = True
        except Exception as e:
            error = str(e)
            logger.error(f"   Deployment failed: {e}")

        duration = time.time() - start_time

        result = BenchmarkResult(
            name=f"deployment_{host}",
            duration=duration,
            success=success,
            metadata={"host": host, "compose_file": compose_file, "error": error},
        )

        self.results.append(result)
        logger.info(f"   Completed in {duration:.2f}s")

        return result

    def benchmark_health_check(
        self, host: str, endpoint: str = "/health"
    ) -> BenchmarkResult:
        """Benchmark health check response time."""
        logger.info(f"🏃 Benchmarking health check on {host}")

        start_time = time.time()
        success = False

        try:
            from vm_tool.health import check_http

            success = check_http(f"http://{host}{endpoint}")
        except Exception as e:
            logger.error(f"   Health check failed: {e}")

        duration = time.time() - start_time

        result = BenchmarkResult(
            name=f"health_check_{host}",
            duration=duration,
            success=success,
            metadata={"host": host, "endpoint": endpoint},
        )

        self.results.append(result)
        logger.info(f"   Response time: {duration*1000:.2f}ms")

        return result

    def run_load_test(
        self, host: str, requests: int = 100, concurrent: int = 10
    ) -> Dict[str, Any]:
        """Run load test against host."""
        logger.info(
            f"🏃 Running load test: {requests} requests, {concurrent} concurrent"
        )

        import concurrent.futures

        durations = []
        successes = 0
        failures = 0

        def make_request():
            start = time.time()
            try:
                from vm_tool.health import check_http

                if check_http(f"http://{host}/"):
                    return time.time() - start, True
            except:
                pass
            return time.time() - start, False

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(requests)]

            for future in concurrent.futures.as_completed(futures):
                duration, success = future.result()
                durations.append(duration)
                if success:
                    successes += 1
                else:
                    failures += 1

        results = {
            "total_requests": requests,
            "successful": successes,
            "failed": failures,
            "success_rate": (successes / requests * 100) if requests > 0 else 0,
            "avg_response_time": mean(durations) if durations else 0,
            "median_response_time": median(durations) if durations else 0,
            "min_response_time": min(durations) if durations else 0,
            "max_response_time": max(durations) if durations else 0,
            "std_dev": stdev(durations) if len(durations) > 1 else 0,
        }

        logger.info(f"   Success rate: {results['success_rate']:.1f}%")
        logger.info(f"   Avg response: {results['avg_response_time']*1000:.2f}ms")

        return results

    def generate_report(self) -> str:
        """Generate benchmark report."""
        if not self.results:
            return "No benchmark results available"

        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        report = f"""
Performance Benchmark Report
===========================
Total Benchmarks: {len(self.results)}
Successful: {len(successful)}
Failed: {len(failed)}

Results:
"""

        for result in self.results:
            status = "✅" if result.success else "❌"
            report += f"\n{status} {result.name}: {result.duration:.3f}s"

        if successful:
            durations = [r.duration for r in successful]
            report += f"""

Statistics (successful runs):
  Average: {mean(durations):.3f}s
  Median: {median(durations):.3f}s
  Min: {min(durations):.3f}s
  Max: {max(durations):.3f}s
"""
            if len(durations) > 1:
                report += f"  Std Dev: {stdev(durations):.3f}s\n"

        return report

    def compare_with_baseline(self, baseline_duration: float) -> Dict[str, Any]:
        """Compare current results with baseline."""
        if not self.results:
            return {"error": "No results to compare"}

        successful = [r for r in self.results if r.success]
        if not successful:
            return {"error": "No successful results"}

        avg_duration = mean([r.duration for r in successful])
        difference = avg_duration - baseline_duration
        percentage_change = (
            (difference / baseline_duration * 100) if baseline_duration > 0 else 0
        )

        return {
            "baseline_duration": baseline_duration,
            "current_avg_duration": avg_duration,
            "difference": difference,
            "percentage_change": percentage_change,
            "improved": difference < 0,
        }
