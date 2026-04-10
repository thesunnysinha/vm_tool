"""Tests for Kubernetes deployment functionality."""

import base64
import os
import tempfile
from unittest.mock import MagicMock, patch, mock_open

import pytest

from vm_tool.core.runner import SetupRunner, SetupRunnerConfig


@pytest.fixture
def runner():
    """Create a SetupRunner with dummy config."""
    config = SetupRunnerConfig(github_project_url="dummy")
    return SetupRunner(config)


@pytest.fixture
def temp_manifest():
    """Create a temporary K8s manifest file."""
    content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: test-app
        image: nginx:latest
        ports:
        - containerPort: 80
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_helm_values():
    """Create a temporary Helm values file."""
    content = """
replicaCount: 2
image:
  repository: nginx
  tag: latest
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


class TestK8sDeployValidation:
    """Test input validation for K8s deployment."""

    def test_manifest_required_for_manifest_method(self, runner):
        """Manifest path is required when method is 'manifest'."""
        with pytest.raises(ValueError, match="--manifest is required"):
            runner.run_k8s_deploy(deploy_method="manifest", manifest=None)

    def test_manifest_must_exist(self, runner):
        """Manifest file must exist on disk."""
        with pytest.raises(FileNotFoundError, match="Manifest not found"):
            runner.run_k8s_deploy(
                deploy_method="manifest", manifest="/nonexistent/manifest.yml"
            )

    def test_helm_chart_required_for_helm_method(self, runner):
        """Helm chart is required when method is 'helm'."""
        with pytest.raises(ValueError, match="--helm-chart is required"):
            runner.run_k8s_deploy(deploy_method="helm", helm_chart=None)

    def test_helm_release_required_for_helm_method(self, runner):
        """Helm release name is required when method is 'helm'."""
        with pytest.raises(ValueError, match="--helm-release is required"):
            runner.run_k8s_deploy(
                deploy_method="helm", helm_chart="nginx", helm_release=None
            )

    def test_helm_values_must_exist(self, runner):
        """Helm values file must exist if specified."""
        with pytest.raises(FileNotFoundError, match="Helm values file not found"):
            runner.run_k8s_deploy(
                deploy_method="helm",
                helm_chart="nginx",
                helm_release="my-nginx",
                helm_values="/nonexistent/values.yml",
            )

    def test_invalid_deploy_method(self, runner):
        """Unknown deploy method raises ValueError."""
        with pytest.raises(ValueError, match="Unknown deploy method"):
            runner.run_k8s_deploy(deploy_method="unknown")


class TestK8sDeployExecution:
    """Test K8s deployment execution."""

    @patch("ansible_runner.run")
    def test_manifest_deploy_calls_ansible(self, mock_run, runner, temp_manifest):
        """Manifest deployment calls Ansible with correct extravars."""
        mock_run.return_value = MagicMock(status="successful", rc=0)

        runner.run_k8s_deploy(
            deploy_method="manifest",
            manifest=temp_manifest,
            namespace="test-ns",
            host="10.0.0.1",
            user="ubuntu",
            force=True,
        )

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        extravars = call_kwargs.kwargs.get("extravars") or call_kwargs[1].get(
            "extravars"
        )
        assert extravars["deploy_method"] == "manifest"
        assert extravars["k8s_namespace"] == "test-ns"
        assert extravars["k8s_manifest"] == os.path.abspath(temp_manifest)
        assert extravars["dry_run"] is False

    @patch("ansible_runner.run")
    def test_helm_deploy_calls_ansible(self, mock_run, runner, temp_helm_values):
        """Helm deployment calls Ansible with correct extravars."""
        mock_run.return_value = MagicMock(status="successful", rc=0)

        runner.run_k8s_deploy(
            deploy_method="helm",
            helm_chart="bitnami/nginx",
            helm_release="my-nginx",
            helm_values=temp_helm_values,
            namespace="prod",
            host="10.0.0.1",
            user="ubuntu",
            force=True,
        )

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        extravars = call_kwargs.kwargs.get("extravars") or call_kwargs[1].get(
            "extravars"
        )
        assert extravars["deploy_method"] == "helm"
        assert extravars["helm_chart"] == "bitnami/nginx"
        assert extravars["helm_release"] == "my-nginx"
        assert extravars["helm_values"] == os.path.abspath(temp_helm_values)
        assert extravars["k8s_namespace"] == "prod"

    @patch("ansible_runner.run")
    def test_dry_run_sets_flag(self, mock_run, runner, temp_manifest):
        """Dry-run flag is passed to Ansible."""
        mock_run.return_value = MagicMock(status="successful", rc=0)

        runner.run_k8s_deploy(
            deploy_method="manifest",
            manifest=temp_manifest,
            dry_run=True,
        )

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        extravars = call_kwargs.kwargs.get("extravars") or call_kwargs[1].get(
            "extravars"
        )
        assert extravars["dry_run"] is True

    @patch("ansible_runner.run")
    def test_custom_kubeconfig(self, mock_run, runner, temp_manifest):
        """Custom kubeconfig path is passed to Ansible."""
        mock_run.return_value = MagicMock(status="successful", rc=0)

        runner.run_k8s_deploy(
            deploy_method="manifest",
            manifest=temp_manifest,
            kubeconfig="/home/user/.kube/custom-config",
        )

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        extravars = call_kwargs.kwargs.get("extravars") or call_kwargs[1].get(
            "extravars"
        )
        assert "kubeconfig_path" in extravars

    @patch("ansible_runner.run")
    def test_default_timeout(self, mock_run, runner, temp_manifest):
        """Default rollout timeout is 300s."""
        mock_run.return_value = MagicMock(status="successful", rc=0)

        runner.run_k8s_deploy(
            deploy_method="manifest",
            manifest=temp_manifest,
        )

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        extravars = call_kwargs.kwargs.get("extravars") or call_kwargs[1].get(
            "extravars"
        )
        assert extravars["rollout_timeout"] == "300s"


class TestK8sDeployIdempotency:
    """Test K8s deployment idempotency."""

    @patch("ansible_runner.run")
    def test_skips_when_no_changes(self, mock_run, runner, temp_manifest, capsys, tmp_path):
        """Deployment is skipped when manifest hasn't changed."""
        from vm_tool.core.state import DeploymentState

        mock_run.return_value = MagicMock(status="successful", rc=0)
        state_dir = tmp_path / ".vm_tool"
        history_dir = tmp_path / ".vm_tool_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        with patch("vm_tool.core.state.DeploymentState", lambda *a, **kw: DeploymentState(state_dir)), \
             patch("vm_tool.core.history.DeploymentHistory") as mock_history_cls:
            mock_history_cls.return_value = MagicMock()

            # First deploy
            runner.run_k8s_deploy(
                deploy_method="manifest",
                manifest=temp_manifest,
                host="10.0.0.1",
                user="ubuntu",
            )

            # Second deploy (no changes)
            runner.run_k8s_deploy(
                deploy_method="manifest",
                manifest=temp_manifest,
                host="10.0.0.1",
                user="ubuntu",
            )

        # Ansible should only be called once
        assert mock_run.call_count == 1
        captured = capsys.readouterr()
        assert "No changes detected" in captured.out

    @patch("ansible_runner.run")
    def test_force_redeploys(self, mock_run, runner, temp_manifest, tmp_path):
        """Force flag causes redeployment even without changes."""
        from vm_tool.core.state import DeploymentState

        mock_run.return_value = MagicMock(status="successful", rc=0)
        state_dir = tmp_path / ".vm_tool"

        with patch("vm_tool.core.state.DeploymentState", lambda *a, **kw: DeploymentState(state_dir)), \
             patch("vm_tool.core.history.DeploymentHistory") as mock_history_cls:
            mock_history_cls.return_value = MagicMock()

            # First deploy
            runner.run_k8s_deploy(
                deploy_method="manifest",
                manifest=temp_manifest,
                host="10.0.0.1",
                user="ubuntu",
            )

            # Second deploy with force
            runner.run_k8s_deploy(
                deploy_method="manifest",
                manifest=temp_manifest,
                host="10.0.0.1",
                user="ubuntu",
                force=True,
            )

        assert mock_run.call_count == 2


class TestImageSubstitution:
    """Test --image placeholder substitution."""

    def test_substitute_single_image(self, runner, tmp_path):
        """Single image placeholder is replaced."""
        manifest = tmp_path / "deployment.yaml"
        manifest.write_text(
            "image: IMAGE_REGISTRY/app:IMAGE_TAG\n"
            "name: app\n"
        )

        result_dir = SetupRunner._substitute_images(
            str(manifest),
            ["IMAGE_REGISTRY/app:IMAGE_TAG=ghcr.io/user/app:sha-abc123"],
        )

        result_file = os.path.join(result_dir, "deployment.yaml")
        assert os.path.exists(result_file)
        content = open(result_file).read()
        assert "ghcr.io/user/app:sha-abc123" in content
        assert "IMAGE_REGISTRY" not in content

        # Cleanup
        import shutil
        shutil.rmtree(result_dir)

    def test_substitute_directory(self, runner, tmp_path):
        """Substitution works on a directory of manifests."""
        (tmp_path / "backend").mkdir()
        (tmp_path / "backend" / "deploy.yaml").write_text(
            "image: PLACEHOLDER:TAG\n"
        )
        (tmp_path / "db").mkdir()
        (tmp_path / "db" / "deploy.yaml").write_text(
            "image: postgres:16\n"
        )

        result_dir = SetupRunner._substitute_images(
            str(tmp_path),
            ["PLACEHOLDER:TAG=myrepo/app:v2"],
        )

        backend = open(os.path.join(result_dir, "backend", "deploy.yaml")).read()
        db = open(os.path.join(result_dir, "db", "deploy.yaml")).read()
        assert "myrepo/app:v2" in backend
        assert "postgres:16" in db  # Unchanged

        import shutil
        shutil.rmtree(result_dir)

    def test_invalid_image_format(self, runner):
        """Invalid --image format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid --image format"):
            SetupRunner._substitute_images("/tmp", ["no-equals-sign"])


class TestSecretParsing:
    """Test --k8s-secret and --registry-secret parsing."""

    def test_parse_generic_secret(self):
        """Parse generic secret from env string."""
        result = SetupRunner._parse_k8s_secrets(
            ["backend-secret=DB_HOST=localhost\nDB_PORT=5432"]
        )
        assert len(result) == 1
        assert result[0]["name"] == "backend-secret"
        assert "DB_HOST=localhost" in result[0]["data"]

    def test_parse_multiple_secrets(self):
        """Parse multiple generic secrets."""
        result = SetupRunner._parse_k8s_secrets([
            "backend-secret=KEY=val",
            "db-secret=PG_PASS=secret",
        ])
        assert len(result) == 2
        assert result[0]["name"] == "backend-secret"
        assert result[1]["name"] == "db-secret"

    def test_invalid_secret_format(self):
        """Invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid --k8s-secret"):
            SetupRunner._parse_k8s_secrets(["no-equals"])

    def test_parse_registry_secret(self):
        """Parse docker-registry secret."""
        result = SetupRunner._parse_registry_secrets(
            ["ghcr-secret=ghcr.io:myuser:ghp_token123"]
        )
        assert len(result) == 1
        assert result[0]["name"] == "ghcr-secret"
        assert result[0]["server"] == "ghcr.io"
        assert result[0]["username"] == "myuser"
        assert result[0]["password"] == "ghp_token123"

    def test_invalid_registry_format(self):
        """Invalid registry format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid --registry-secret"):
            SetupRunner._parse_registry_secrets(["no-equals"])

    def test_registry_missing_parts(self):
        """Registry secret with wrong number of colon parts raises."""
        with pytest.raises(ValueError, match="3 colon-separated parts"):
            SetupRunner._parse_registry_secrets(["name=server:user"])


class TestKubeconfigB64:
    """Test --kubeconfig-b64 decoding."""

    @patch("ansible_runner.run")
    def test_kubeconfig_b64_decoded(self, mock_run, runner, temp_manifest):
        """Base64 kubeconfig is decoded to a temp file."""
        mock_run.return_value = MagicMock(status="successful", rc=0)
        kubeconfig_content = b"apiVersion: v1\nclusters: []\n"
        b64 = base64.b64encode(kubeconfig_content).decode()

        runner.run_k8s_deploy(
            deploy_method="manifest",
            manifest=temp_manifest,
            kubeconfig_b64=b64,
            force=True,
        )

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        extravars = call_kwargs.kwargs.get("extravars") or call_kwargs[1].get("extravars")
        # kubeconfig_path should point to a file (may be cleaned up already)
        assert "kubeconfig_path" in extravars

    @patch("ansible_runner.run")
    def test_kubeconfig_b64_cleanup(self, mock_run, runner, temp_manifest):
        """Temp kubeconfig file is cleaned up after deployment."""
        mock_run.return_value = MagicMock(status="successful", rc=0)
        b64 = base64.b64encode(b"test").decode()

        runner.run_k8s_deploy(
            deploy_method="manifest",
            manifest=temp_manifest,
            kubeconfig_b64=b64,
            force=True,
        )

        # Verify no leaked temp files with .kubeconfig suffix
        import glob
        leaked = glob.glob("/tmp/*.kubeconfig")
        assert len(leaked) == 0, f"Leaked kubeconfig files: {leaked}"
