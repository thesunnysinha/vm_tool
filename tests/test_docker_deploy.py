"""Tests for run_docker_deploy() — previously untested critical code path."""
import os
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from vm_tool.core.runner import SetupRunner, SetupRunnerConfig


@pytest.fixture
def tmp_compose(tmp_path):
    """A minimal docker-compose.yml in a temp directory."""
    compose = tmp_path / "docker-compose.yml"
    compose.write_text("version: '3'\nservices:\n  app:\n    image: nginx\n")
    return str(compose)


@pytest.fixture
def runner():
    return SetupRunner(SetupRunnerConfig())


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Redirect DeploymentState to a per-test temp dir so hash checks start fresh."""
    from vm_tool.core import state as state_mod

    original_init = state_mod.DeploymentState.__init__

    def patched_init(self, state_dir=None):
        original_init(self, state_dir=tmp_path / "vm_tool_state")

    monkeypatch.setattr(state_mod.DeploymentState, "__init__", patched_init)


class TestDockerDeployExecution:
    @patch("ansible_runner.run")
    def test_docker_deploy_calls_ansible(self, mock_run, runner, tmp_compose):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1", user="ubuntu", force=True)
        mock_run.assert_called_once()
        kwargs = mock_run.call_args[1]
        assert kwargs["extravars"]["DOCKER_COMPOSE_FILE_PATH"] == tmp_compose
        assert kwargs["extravars"]["DEPLOY_MODE"] == "push"

    @patch("ansible_runner.run")
    def test_docker_deploy_passes_host_and_user(self, mock_run, runner, tmp_compose):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1", user="deploy", force=True)
        mock_run.assert_called_once()
        kwargs = mock_run.call_args[1]
        # Inventory path should be a temp file, not the fixed path
        inventory_path = kwargs["inventory"]
        assert "generated_inventory.yml" not in inventory_path

    @patch("ansible_runner.run")
    def test_docker_deploy_uses_accept_new_host_key_checking(self, mock_run, runner, tmp_compose):
        import yaml
        captured_inventory = {}

        def capture_run(**kwargs):
            with open(kwargs["inventory"]) as f:
                captured_inventory.update(yaml.safe_load(f))
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run
        runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1", force=True)

        ssh_args = (
            captured_inventory["all"]["hosts"]["target_host"]["ansible_ssh_common_args"]
        )
        assert "accept-new" in ssh_args
        assert "StrictHostKeyChecking=no" not in ssh_args

    @patch("ansible_runner.run")
    def test_docker_deploy_temp_inventory_cleaned_up(self, mock_run, runner, tmp_compose):
        inventory_paths = []

        def capture_run(**kwargs):
            inventory_paths.append(kwargs["inventory"])
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run
        runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1", force=True)

        assert len(inventory_paths) == 1
        assert not os.path.exists(inventory_paths[0]), "Temp inventory not cleaned up"

    @patch("ansible_runner.run")
    def test_docker_deploy_temp_inventory_cleaned_up_on_failure(self, mock_run, runner, tmp_compose):
        inventory_paths = []

        def capture_run(**kwargs):
            inventory_paths.append(kwargs["inventory"])
            return MagicMock(status="failed", rc=1)

        mock_run.side_effect = capture_run
        with pytest.raises(RuntimeError):
            runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1", force=True)

        assert not os.path.exists(inventory_paths[0]), "Temp inventory not cleaned up on failure"

    @patch("ansible_runner.run")
    def test_docker_deploy_skips_when_no_changes(self, mock_run, runner, tmp_compose, capsys):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1")
        runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1")
        # Second call skipped due to hash match
        assert mock_run.call_count == 1
        captured = capsys.readouterr()
        assert "No changes" in captured.out

    @patch("ansible_runner.run")
    def test_docker_deploy_force_bypasses_hash_check(self, mock_run, runner, tmp_compose):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1")
        runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1", force=True)
        assert mock_run.call_count == 2

    @patch("ansible_runner.run")
    def test_docker_deploy_records_history_on_success(self, mock_run, runner, tmp_compose):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        with patch("vm_tool.core.history.DeploymentHistory") as mock_hist_cls:
            mock_hist = MagicMock()
            mock_hist_cls.return_value = mock_hist
            runner.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1", force=True)

        mock_hist.record_deployment.assert_called_once()
        call_kwargs = mock_hist.record_deployment.call_args[1]
        assert call_kwargs["host"] == "10.0.0.1"
        assert call_kwargs["status"] == "success"

    @patch("ansible_runner.run")
    def test_docker_deploy_marks_state_failed_on_error(self, mock_run, runner, tmp_compose):
        mock_run.return_value = MagicMock(status="failed", rc=1)
        with patch("vm_tool.core.state.DeploymentState") as mock_state_cls:
            mock_state = MagicMock()
            mock_state.compute_hash.return_value = "abc123"
            mock_state.needs_update.return_value = True
            mock_state_cls.return_value = mock_state
            with pytest.raises(RuntimeError):
                runner.run_docker_deploy(
                    compose_file=tmp_compose, host="10.0.0.1", force=True
                )
            mock_state.mark_failed.assert_called_once()

    @patch("ansible_runner.run")
    def test_docker_deploy_no_host_uses_provided_inventory(self, mock_run, runner, tmp_compose, tmp_path):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        inv = tmp_path / "inventory.yml"
        inv.write_text("all:\n  hosts:\n    myhost: {}\n")
        runner.run_docker_deploy(
            compose_file=tmp_compose,
            inventory_file=str(inv),
            force=True,
        )
        kwargs = mock_run.call_args[1]
        assert kwargs["inventory"] == str(inv)

    @patch("ansible_runner.run")
    def test_docker_deploy_github_token_not_in_extravars(self, mock_run, runner, tmp_compose):
        """GitHub token must be passed via envvars, not extravars."""
        config = SetupRunnerConfig(
            github_username="user",
            github_token="ghp_supersecret",
        )
        runner2 = SetupRunner(config)
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner2.run_docker_deploy(compose_file=tmp_compose, host="10.0.0.1", force=True)

        kwargs = mock_run.call_args[1]
        extravars_str = str(kwargs.get("extravars", {}))
        envvars = kwargs.get("envvars", {})

        assert "ghp_supersecret" not in extravars_str
        assert envvars.get("VM_TOOL_GITHUB_TOKEN") == "ghp_supersecret"


class TestConcurrentSafety:
    @patch("ansible_runner.run")
    def test_concurrent_docker_deploys_use_separate_inventory_files(
        self, mock_run, tmp_path
    ):
        """Two simultaneous deploy-docker calls must not share inventory files."""
        inventory_paths = []
        lock = threading.Lock()

        def capture_run(**kwargs):
            with lock:
                inventory_paths.append(kwargs["inventory"])
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run

        compose1 = tmp_path / "dc1.yml"
        compose1.write_text("version: '3'\nservices:\n  a:\n    image: nginx\n")
        compose2 = tmp_path / "dc2.yml"
        compose2.write_text("version: '3'\nservices:\n  b:\n    image: nginx\n")

        runner1 = SetupRunner(SetupRunnerConfig())
        runner2 = SetupRunner(SetupRunnerConfig())

        t1 = threading.Thread(
            target=runner1.run_docker_deploy,
            kwargs={"compose_file": str(compose1), "host": "10.0.0.1", "force": True},
        )
        t2 = threading.Thread(
            target=runner2.run_docker_deploy,
            kwargs={"compose_file": str(compose2), "host": "10.0.0.2", "force": True},
        )
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(inventory_paths) == 2
        assert inventory_paths[0] != inventory_paths[1], (
            "Concurrent deploys used the same inventory file"
        )
        # Both paths are temp files, not the old shared path
        for path in inventory_paths:
            assert "generated_inventory.yml" not in path
