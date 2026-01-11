import os

import pytest

from vm_tool.runner import SetupRunner, SetupRunnerConfig


def test_config_validation():
    # Valid config
    config = SetupRunnerConfig(
        github_project_url="https://github.com/user/repo", github_branch="main"
    )
    assert config.github_project_url == "https://github.com/user/repo"

    # Invalid config: github_username without token
    with pytest.raises(ValueError):
        SetupRunnerConfig(
            github_project_url="https://github.com/user/repo", github_username="user"
        )

    # Invalid config: dockerhub_username without password
    with pytest.raises(ValueError):
        SetupRunnerConfig(
            github_project_url="https://github.com/user/repo", dockerhub_username="user"
        )


def test_run_setup(mock_ansible_runner, mock_fs):
    mock_run = mock_ansible_runner
    mock_run.return_value.rc = 0

    config = SetupRunnerConfig(github_project_url="https://github.com/user/repo")
    runner = SetupRunner(config)
    runner.run_setup()

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "extravars" in kwargs
    assert kwargs["extravars"]["GITHUB_PROJECT_URL"] == "https://github.com/user/repo"


def test_run_setup_failure(mock_ansible_runner, mock_fs):
    mock_run = mock_ansible_runner
    mock_run.return_value.rc = 1
    mock_run.return_value.stdout = "Error"

    config = SetupRunnerConfig(github_project_url="https://github.com/user/repo")
    runner = SetupRunner(config)

    with pytest.raises(RuntimeError, match="Ansible playbook execution failed"):
        runner.run_setup()
