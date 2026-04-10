"""Tests for run_cloud_setup() — inventory generation, credential security, cleanup."""
import os
from unittest.mock import MagicMock, patch

import pytest
import yaml

from vm_tool.core.runner import SetupRunner, SetupRunnerConfig, SSHConfig


@pytest.fixture
def runner():
    return SetupRunner(
        SetupRunnerConfig(
            github_project_url="https://github.com/example/repo",
            github_username="user",
            github_token="ghp_dummy",
        )
    )


@pytest.fixture
def ssh_key_config(tmp_path):
    key = tmp_path / "id_rsa"
    key.write_text("PRIVATE KEY")
    return SSHConfig(
        ssh_hostname="10.0.0.1",
        ssh_username="ubuntu",
        ssh_identity_file=str(key),
    )


@pytest.fixture
def ssh_password_config():
    return SSHConfig(
        ssh_hostname="10.0.0.2",
        ssh_username="deploy",
        ssh_password="s3cret!",
    )


@pytest.fixture
def ssh_password_config2():
    return SSHConfig(
        ssh_hostname="10.0.0.3",
        ssh_username="admin",
        ssh_password="different!",
    )


class TestCloudSetupInventory:
    @patch("ansible_runner.run")
    def test_inventory_contains_all_ssh_configs(self, mock_run, runner, ssh_key_config, ssh_password_config):
        """Every SSHConfig should appear as a host in the generated inventory."""
        captured = {}

        def capture_run(**kwargs):
            with open(kwargs["inventory"]) as f:
                captured.update(yaml.safe_load(f))
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run
        runner.run_cloud_setup([ssh_key_config, ssh_password_config])

        hosts = captured["all"]["hosts"]
        assert len(hosts) == 2
        host_ips = {v["ansible_host"] for v in hosts.values()}
        assert "10.0.0.1" in host_ips
        assert "10.0.0.2" in host_ips

    @patch("ansible_runner.run")
    def test_ssh_key_written_to_inventory(self, mock_run, runner, ssh_key_config):
        captured = {}

        def capture_run(**kwargs):
            with open(kwargs["inventory"]) as f:
                captured.update(yaml.safe_load(f))
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run
        runner.run_cloud_setup([ssh_key_config])

        host = next(iter(captured["all"]["hosts"].values()))
        assert "ansible_ssh_private_key_file" in host

    @patch("ansible_runner.run")
    def test_password_written_per_host_in_inventory(self, mock_run, runner, ssh_password_config):
        """SSH password is written as ansible_ssh_pass per-host in the 0o600 temp inventory."""
        captured = {}

        def capture_run(**kwargs):
            with open(kwargs["inventory"]) as f:
                captured.update(yaml.safe_load(f))
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run
        runner.run_cloud_setup([ssh_password_config])

        host = next(iter(captured["all"]["hosts"].values()))
        assert host.get("ansible_ssh_pass") == "s3cret!"

    @patch("ansible_runner.run")
    def test_multiple_hosts_different_passwords(self, mock_run, runner, ssh_password_config, ssh_password_config2):
        """Each host gets its own password — no last-wins behaviour."""
        captured = {}

        def capture_run(**kwargs):
            with open(kwargs["inventory"]) as f:
                captured.update(yaml.safe_load(f))
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run
        runner.run_cloud_setup([ssh_password_config, ssh_password_config2])

        hosts = captured["all"]["hosts"]
        passwords = {v["ansible_host"]: v.get("ansible_ssh_pass") for v in hosts.values()}
        assert passwords["10.0.0.2"] == "s3cret!"
        assert passwords["10.0.0.3"] == "different!"

    @patch("ansible_runner.run")
    def test_password_not_in_extravars(self, mock_run, runner, ssh_password_config):
        """Passwords must never appear in extravars (which are logged by ansible-runner)."""
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run_cloud_setup([ssh_password_config])

        kwargs = mock_run.call_args[1]
        extravars_str = str(kwargs.get("extravars", {}))
        assert "s3cret!" not in extravars_str

    @patch("ansible_runner.run")
    def test_inventory_file_is_mode_600(self, mock_run, runner, ssh_password_config):
        """Inventory file containing passwords must be 0o600."""
        captured_paths = []

        def capture_run(**kwargs):
            captured_paths.append(kwargs["inventory"])
            # Check permissions while file still exists
            mode = oct(os.stat(kwargs["inventory"]).st_mode)[-3:]
            captured_paths.append(mode)
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run
        runner.run_cloud_setup([ssh_password_config])

        assert captured_paths[1] == "600", f"Inventory file permissions: {captured_paths[1]}, expected 600"

    @patch("ansible_runner.run")
    def test_inventory_temp_file_cleaned_up_on_success(self, mock_run, runner, ssh_key_config):
        inventory_paths = []

        def capture_run(**kwargs):
            inventory_paths.append(kwargs["inventory"])
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture_run
        runner.run_cloud_setup([ssh_key_config])

        assert len(inventory_paths) == 1
        assert not os.path.exists(inventory_paths[0]), "Temp inventory not cleaned up after success"

    @patch("ansible_runner.run")
    def test_inventory_temp_file_cleaned_up_on_failure(self, mock_run, runner, ssh_key_config):
        inventory_paths = []

        def capture_run(**kwargs):
            inventory_paths.append(kwargs["inventory"])
            return MagicMock(status="failed", rc=1)

        mock_run.side_effect = capture_run
        with pytest.raises(RuntimeError):
            runner.run_cloud_setup([ssh_key_config])

        assert not os.path.exists(inventory_paths[0]), "Temp inventory not cleaned up after failure"

    @patch("ansible_runner.run")
    def test_inventory_is_not_fixed_path(self, mock_run, runner, ssh_key_config):
        """Inventory must use a temp path, not the old fixed generated_inventory.yml."""
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run_cloud_setup([ssh_key_config])

        kwargs = mock_run.call_args[1]
        assert "generated_inventory.yml" not in kwargs["inventory"]
        assert "dynamic_inventory.yml" not in kwargs["inventory"]

    @patch("ansible_runner.run")
    def test_github_token_not_in_extravars(self, mock_run, ssh_key_config):
        """GitHub token must be in envvars, never in extravars."""
        config = SetupRunnerConfig(
            github_project_url="https://github.com/example/repo",
            github_username="user",
            github_token="ghp_topsecret",
        )
        runner = SetupRunner(config)
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run_cloud_setup([ssh_key_config])

        kwargs = mock_run.call_args[1]
        extravars_str = str(kwargs.get("extravars", {}))
        envvars = kwargs.get("envvars", {})

        assert "ghp_topsecret" not in extravars_str
        assert envvars.get("VM_TOOL_GITHUB_TOKEN") == "ghp_topsecret"

    def test_requires_github_url(self, ssh_key_config):
        """run_cloud_setup must raise if github_project_url is not set."""
        runner = SetupRunner(SetupRunnerConfig())
        with pytest.raises(ValueError, match="github_project_url"):
            runner.run_cloud_setup([ssh_key_config])
