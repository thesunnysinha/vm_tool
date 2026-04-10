"""Blue-Green deployment strategy for zero-downtime deployments."""

import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class BlueGreenDeployment:
    """Manage blue-green deployments for zero-downtime updates."""

    def __init__(
        self,
        blue_host: str,
        green_host: str,
        load_balancer_host: Optional[str] = None,
        health_check_url: str = "/health",
        health_check_timeout: int = 300,
        ssh_user: Optional[str] = None,
    ):
        """Initialize blue-green deployment.

        Args:
            blue_host: Blue environment host
            green_host: Green environment host
            load_balancer_host: Load balancer host (if using external LB)
            health_check_url: Health check endpoint
            health_check_timeout: Max time to wait for health checks (seconds)
            ssh_user: SSH user for connecting to blue/green hosts
        """
        self.blue_host = blue_host
        self.green_host = green_host
        self.load_balancer_host = load_balancer_host
        self.health_check_url = health_check_url
        self.health_check_timeout = health_check_timeout
        self.ssh_user = ssh_user
        self.current_active = "blue"  # Track which environment is active

    def deploy(
        self,
        compose_file: str,
        target_env: Optional[str] = None,
        auto_switch: bool = True,
    ) -> Dict[str, Any]:
        """Execute blue-green deployment.

        Args:
            compose_file: Path to docker-compose file
            target_env: Target environment ('blue' or 'green'), auto-detect if None
            auto_switch: Automatically switch traffic after successful deployment

        Returns:
            Deployment result with status and details
        """
        # Determine target environment (deploy to inactive)
        if target_env is None:
            target_env = "green" if self.current_active == "blue" else "blue"

        target_host = self.green_host if target_env == "green" else self.blue_host

        logger.info(f"🔵🟢 Starting blue-green deployment to {target_env} environment")
        logger.info(f"   Target: {target_host}")
        logger.info(f"   Current active: {self.current_active}")

        result = {
            "success": False,
            "target_env": target_env,
            "target_host": target_host,
            "previous_active": self.current_active,
            "switched": False,
        }

        try:
            # Step 1: Deploy to target environment
            logger.info(f"📦 Deploying to {target_env} environment...")
            self._deploy_to_host(target_host, compose_file)

            # Step 2: Run health checks
            logger.info(f"🏥 Running health checks on {target_env}...")
            if not self._wait_for_health(target_host):
                raise Exception(f"Health checks failed on {target_env} environment")

            logger.info(f"✅ {target_env.capitalize()} environment is healthy")

            # Step 3: Switch traffic (if auto_switch enabled)
            if auto_switch:
                logger.info(f"🔄 Switching traffic to {target_env}...")
                self._switch_traffic(target_env)
                result["switched"] = True
                self.current_active = target_env
                logger.info(f"✅ Traffic switched to {target_env}")
            else:
                logger.info(f"⏸️  Auto-switch disabled. Manual switch required.")

            result["success"] = True
            return result

        except Exception as e:
            logger.error(f"❌ Blue-green deployment failed: {e}")
            result["error"] = str(e)
            return result

    def switch_traffic(self, target_env: str) -> bool:
        """Manually switch traffic to specified environment.

        Args:
            target_env: Target environment ('blue' or 'green')

        Returns:
            True if switch successful, False otherwise
        """
        try:
            self._switch_traffic(target_env)
            self.current_active = target_env
            logger.info(f"✅ Traffic switched to {target_env}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to switch traffic: {e}")
            return False

    def rollback(self) -> bool:
        """Rollback to previous environment.

        Returns:
            True if rollback successful, False otherwise
        """
        previous_env = "green" if self.current_active == "blue" else "blue"
        logger.info(f"🔄 Rolling back to {previous_env} environment...")
        return self.switch_traffic(previous_env)

    def _deploy_to_host(self, host: str, compose_file: str):
        """Deploy application to specified host using Docker Compose."""
        from vm_tool.core.runner import SetupRunner, SetupRunnerConfig
        SetupRunner(SetupRunnerConfig()).run_docker_deploy(
            compose_file=compose_file,
            host=host,
            user=self.ssh_user,
            force=True,
        )

    def _wait_for_health(self, host: str) -> bool:
        """Wait for host to become healthy.

        Args:
            host: Host to check

        Returns:
            True if healthy within timeout, False otherwise
        """
        from vm_tool.deploy.health import check_http

        start_time = time.time()
        url = f"http://{host}{self.health_check_url}"

        while time.time() - start_time < self.health_check_timeout:
            try:
                if check_http(url):
                    return True
            except Exception as e:
                logger.debug(f"Health check failed: {e}")

            time.sleep(5)

        return False

    def _switch_traffic(self, target_env: str):
        """Switch load balancer traffic to target environment.

        Override this method with your load balancer's switch logic.
        See docs/strategies.md for nginx, AWS ALB, and HAProxy examples.

        Args:
            target_env: Target environment ('blue' or 'green')
        """
        target_host = self.green_host if target_env == "green" else self.blue_host
        raise NotImplementedError(
            f"_switch_traffic must be overridden for your load balancer. "
            f"Target: {target_env} ({target_host}). "
            f"See docs/strategies.md for nginx, AWS ALB, and HAProxy examples."
        )


class BlueGreenConfig:
    """Configuration for blue-green deployments."""

    def __init__(self, config_file: str = "blue-green.yml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load blue-green configuration."""
        import yaml

        if not self.config_file.exists():
            return self._default_config()

        with open(self.config_file) as f:
            return yaml.safe_load(f)

    def _default_config(self) -> Dict[str, Any]:
        """Return default blue-green configuration."""
        return {
            "blue": {
                "host": "10.0.1.10",
                "port": 8000,
            },
            "green": {
                "host": "10.0.1.11",
                "port": 8000,
            },
            "load_balancer": {
                "host": "10.0.1.1",
                "type": "nginx",  # or 'aws-alb', 'haproxy'
            },
            "health_check": {
                "url": "/health",
                "timeout": 300,
                "interval": 5,
            },
        }

    def save(self):
        """Save configuration to file."""
        import yaml

        with open(self.config_file, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)
