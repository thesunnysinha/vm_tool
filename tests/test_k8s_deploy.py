"""Tests for Kubernetes deployment functionality."""

import os
import tempfile
from unittest.mock import MagicMock, patch, mock_open

import pytest

from vm_tool.runner import SetupRunner, SetupRunnerConfig


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
        from vm_tool.state import DeploymentState

        mock_run.return_value = MagicMock(status="successful", rc=0)
        state_dir = tmp_path / ".vm_tool"
        history_dir = tmp_path / ".vm_tool_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        def make_state(*a, **kw):
            return DeploymentState(state_dir)

        with patch("vm_tool.state.DeploymentState", lambda *a, **kw: DeploymentState(state_dir)), \
             patch("vm_tool.history.DeploymentHistory") as mock_history_cls:
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
        from vm_tool.state import DeploymentState

        mock_run.return_value = MagicMock(status="successful", rc=0)
        state_dir = tmp_path / ".vm_tool"

        with patch("vm_tool.state.DeploymentState", lambda *a, **kw: DeploymentState(state_dir)), \
             patch("vm_tool.history.DeploymentHistory") as mock_history_cls:
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
