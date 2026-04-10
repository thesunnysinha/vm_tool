"""Kubernetes support: manifest/Helm deploy, pod status, scaling, rollback.

Deploy methods delegate to SetupRunner.run_k8s_deploy() so they share the same
Ansible-based execution path. Pod lifecycle ops (status, scale, rollback) call
kubectl directly via subprocess.

ServiceMeshIntegration and GitOpsIntegration are not yet implemented — they
require Istio/ArgoCD CLI integration that is environment-specific.
"""

import logging
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KubernetesDeployment:
    """Kubernetes deployment manager.

    Example::

        kd = KubernetesDeployment(namespace="myapp", kubeconfig="~/.kube/config")
        kd.deploy_manifest("k8s/")
        print(kd.get_pod_status("myapp-abc123"))  # "Running"
        kd.scale_deployment("myapp", replicas=3)
        kd.rollback_deployment("myapp")
    """

    def __init__(self, kubeconfig: Optional[str] = None, namespace: str = "default"):
        self.kubeconfig = kubeconfig
        self.namespace = namespace
        self._runner = None
        logger.info(f"Kubernetes deployment initialized (namespace: {namespace})")

    def _get_runner(self):
        """Lazy-init SetupRunner to avoid circular imports."""
        if self._runner is None:
            from vm_tool.core.runner import SetupRunner, SetupRunnerConfig
            self._runner = SetupRunner(SetupRunnerConfig())
        return self._runner

    def _kubectl(self, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
        """Run a kubectl command. Raises RuntimeError on non-zero exit."""
        cmd = ["kubectl"]
        if self.kubeconfig:
            cmd.extend(["--kubeconfig", self.kubeconfig])
        cmd.extend(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            raise RuntimeError(
                f"kubectl {' '.join(args)} failed: {result.stderr.strip()}"
            )
        return result

    def deploy_manifest(self, manifest_file: str) -> bool:
        """Apply Kubernetes manifests. Returns True on success.

        Args:
            manifest_file: Path to a manifest file or directory of YAML files.
        """
        try:
            self._get_runner().run_k8s_deploy(
                deploy_method="manifest",
                manifest=manifest_file,
                namespace=self.namespace,
                kubeconfig=self.kubeconfig,
                force=True,
            )
            return True
        except Exception as e:
            logger.error(f"Manifest deploy failed: {e}")
            return False

    def deploy_helm_chart(
        self,
        chart_name: str,
        release_name: str,
        values: Dict[str, Any],
    ) -> bool:
        """Deploy or upgrade a Helm chart. Returns True on success.

        Args:
            chart_name: Chart path or repository reference (e.g. 'stable/nginx').
            release_name: Helm release name.
            values: Values dict to pass to the chart.
        """
        import os
        import tempfile
        import yaml

        values_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yml", prefix="vm_tool_helm_values_", delete=False
            ) as f:
                yaml.dump(values, f)
                values_path = f.name

            self._get_runner().run_k8s_deploy(
                deploy_method="helm",
                helm_chart=chart_name,
                helm_release=release_name,
                helm_values=values_path,
                namespace=self.namespace,
                kubeconfig=self.kubeconfig,
                force=True,
            )
            return True
        except Exception as e:
            logger.error(f"Helm deploy failed: {e}")
            return False
        finally:
            if values_path and os.path.exists(values_path):
                try:
                    os.unlink(values_path)
                except OSError:
                    pass

    def get_pod_status(self, pod_name: str) -> str:
        """Return the pod phase string (e.g. 'Running', 'Pending', 'Failed').

        Args:
            pod_name: Full pod name.
        """
        result = self._kubectl(
            "get", "pod", pod_name,
            "-n", self.namespace,
            "-o", "jsonpath={.status.phase}",
        )
        return result.stdout.strip()

    def scale_deployment(self, deployment_name: str, replicas: int) -> bool:
        """Scale a Deployment to the specified replica count.

        Args:
            deployment_name: Name of the Deployment resource.
            replicas: Desired replica count.
        """
        try:
            self._kubectl(
                "scale", "deployment", deployment_name,
                f"--replicas={replicas}",
                "-n", self.namespace,
            )
            logger.info(f"Scaled {deployment_name} to {replicas} replicas")
            return True
        except RuntimeError as e:
            logger.error(f"Scale failed: {e}")
            return False

    def rollback_deployment(
        self, deployment_name: str, revision: Optional[int] = None
    ) -> bool:
        """Roll back a Deployment to a previous revision.

        Args:
            deployment_name: Name of the Deployment resource.
            revision: Specific revision number, or None to roll back to previous.
        """
        try:
            cmd = ["rollout", "undo", f"deployment/{deployment_name}", "-n", self.namespace]
            if revision is not None:
                cmd.append(f"--to-revision={revision}")
            self._kubectl(*cmd)
            logger.info(f"Rolled back {deployment_name}" + (f" to revision {revision}" if revision else ""))
            return True
        except RuntimeError as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_pods(self, label_selector: Optional[str] = None) -> List[Dict[str, str]]:
        """Return list of pod dicts with name and status for this namespace.

        Args:
            label_selector: Optional label selector (e.g. 'app=myapp').
        """
        cmd = [
            "get", "pods", "-n", self.namespace,
            "-o", "jsonpath={range .items[*]}{.metadata.name}|{.status.phase}\\n{end}",
        ]
        if label_selector:
            cmd.extend(["-l", label_selector])
        result = self._kubectl(*cmd)
        pods = []
        for line in result.stdout.strip().splitlines():
            if "|" in line:
                name, status = line.split("|", 1)
                pods.append({"name": name, "status": status})
        return pods


class ServiceMeshIntegration:
    """Service mesh integration (Istio/Linkerd).

    Traffic splitting and mTLS configuration require Istio or another service mesh
    to be installed in the cluster. These operations are environment-specific and
    cannot be implemented generically. Override these methods for your mesh.

    See docs/strategies.md for examples.
    """

    def __init__(self, mesh_type: str = "istio"):
        self.mesh_type = mesh_type
        logger.info(f"Service mesh integration: {mesh_type}")

    def configure_traffic_split(self, service: str, versions: Dict[str, int]) -> bool:
        """Configure traffic splitting between versions.

        Not implemented: requires Istio VirtualService or similar mesh CRDs.
        Override this method for your specific mesh configuration.
        """
        raise NotImplementedError(
            f"Traffic splitting via {self.mesh_type} requires mesh-specific CRDs. "
            f"Override configure_traffic_split() for your {self.mesh_type} setup. "
            f"See docs/strategies.md for an Istio example."
        )

    def enable_mtls(self, namespace: str) -> bool:
        """Enable mutual TLS for a namespace.

        Not implemented: requires Istio PeerAuthentication or similar.
        Override this method for your specific mesh configuration.
        """
        raise NotImplementedError(
            f"mTLS configuration via {self.mesh_type} is mesh-specific. "
            f"Override enable_mtls() for your {self.mesh_type} setup."
        )


class GitOpsIntegration:
    """GitOps integration (ArgoCD/Flux).

    Application creation and sync require ArgoCD or Flux to be installed.
    These operations are environment-specific. Override for your GitOps tool.

    See docs/strategies.md for ArgoCD CLI examples.
    """

    def __init__(self, gitops_tool: str = "argocd"):
        self.gitops_tool = gitops_tool
        logger.info(f"GitOps integration: {gitops_tool}")

    def create_application(self, name: str, repo_url: str, path: str) -> bool:
        """Create a GitOps application.

        Not implemented: requires ArgoCD/Flux CLI or API integration.
        Override this method for your specific GitOps tool.
        """
        raise NotImplementedError(
            f"GitOps application creation via {self.gitops_tool} requires the "
            f"{self.gitops_tool} CLI or API. "
            f"Override create_application() for your setup. "
            f"See docs/strategies.md for an ArgoCD example."
        )

    def sync_application(self, name: str) -> bool:
        """Sync a GitOps application.

        Not implemented: requires ArgoCD/Flux CLI or API integration.
        """
        raise NotImplementedError(
            f"GitOps application sync via {self.gitops_tool} requires the "
            f"{self.gitops_tool} CLI or API. "
            f"Override sync_application() for your setup."
        )
