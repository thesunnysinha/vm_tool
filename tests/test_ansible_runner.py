"""Tests for the private AnsibleRunner wrapper."""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from vm_tool.core.ansible import AnsibleRunner


@pytest.fixture
def runner(tmp_path):
    """AnsibleRunner pointed at a temp playbook dir."""
    return AnsibleRunner(playbook_dir=str(tmp_path))


@pytest.fixture
def dummy_playbook(tmp_path):
    """A dummy playbook file so path-resolution works."""
    p = tmp_path / "site.yml"
    p.write_text("---\n- hosts: all\n")
    return str(p)


class TestAnsibleRunnerBehavior:
    @patch("ansible_runner.run")
    def test_success_does_not_raise(self, mock_run, runner, dummy_playbook):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run(
            playbook=dummy_playbook,
            inventory="/tmp/inv.yml",
            extravars={},
        )
        mock_run.assert_called_once()

    @patch("ansible_runner.run")
    def test_rc_nonzero_raises_runtime_error(self, mock_run, runner, dummy_playbook):
        mock_run.return_value = MagicMock(status="failed", rc=1)
        with pytest.raises(RuntimeError, match="failed"):
            runner.run(
                playbook=dummy_playbook,
                inventory="/tmp/inv.yml",
                extravars={},
            )

    @patch("ansible_runner.run")
    def test_private_data_dir_cleaned_up_on_success(self, mock_run, runner, dummy_playbook):
        captured_dirs = []

        def capture(**kwargs):
            captured_dirs.append(kwargs["private_data_dir"])
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture
        runner.run(playbook=dummy_playbook, inventory="/tmp/inv.yml", extravars={})

        assert len(captured_dirs) == 1
        assert not os.path.exists(captured_dirs[0]), "private_data_dir not cleaned up on success"

    @patch("ansible_runner.run")
    def test_private_data_dir_cleaned_up_on_failure(self, mock_run, runner, dummy_playbook):
        captured_dirs = []

        def capture(**kwargs):
            captured_dirs.append(kwargs["private_data_dir"])
            return MagicMock(status="failed", rc=2)

        mock_run.side_effect = capture
        with pytest.raises(RuntimeError):
            runner.run(playbook=dummy_playbook, inventory="/tmp/inv.yml", extravars={})

        assert not os.path.exists(captured_dirs[0]), "private_data_dir not cleaned up on failure"

    @patch("ansible_runner.run")
    def test_envvars_passed_through(self, mock_run, runner, dummy_playbook):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run(
            playbook=dummy_playbook,
            inventory="/tmp/inv.yml",
            extravars={"KEY": "val"},
            envvars={"SECRET_TOKEN": "s3cr3t"},
        )
        kwargs = mock_run.call_args[1]
        assert kwargs["envvars"]["SECRET_TOKEN"] == "s3cr3t"

    @patch("ansible_runner.run")
    def test_envvars_defaults_to_empty_dict(self, mock_run, runner, dummy_playbook):
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run(playbook=dummy_playbook, inventory="/tmp/inv.yml", extravars={})
        kwargs = mock_run.call_args[1]
        assert kwargs["envvars"] == {}

    @patch("ansible_runner.run")
    def test_relative_playbook_resolved_against_playbook_dir(self, mock_run, runner, tmp_path):
        """Relative playbook names are resolved relative to playbook_dir."""
        playbook = tmp_path / "deploy.yml"
        playbook.write_text("---\n")
        mock_run.return_value = MagicMock(status="successful", rc=0)
        runner.run(playbook="deploy.yml", inventory="/tmp/inv.yml", extravars={})
        kwargs = mock_run.call_args[1]
        assert os.path.isabs(kwargs["playbook"])
        assert kwargs["playbook"].endswith("deploy.yml")

    @patch("ansible_runner.run")
    def test_each_run_uses_unique_private_data_dir(self, mock_run, runner, dummy_playbook):
        dirs = []

        def capture(**kwargs):
            dirs.append(kwargs["private_data_dir"])
            return MagicMock(status="successful", rc=0)

        mock_run.side_effect = capture
        runner.run(playbook=dummy_playbook, inventory="/tmp/inv.yml", extravars={})
        runner.run(playbook=dummy_playbook, inventory="/tmp/inv.yml", extravars={})
        assert dirs[0] != dirs[1], "Two runs shared the same private_data_dir"
