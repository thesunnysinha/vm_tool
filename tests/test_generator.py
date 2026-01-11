import pytest
import os
from unittest.mock import patch, mock_open
from vm_tool.generator import PipelineGenerator


def test_generate_github_pipeline(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    generator = PipelineGenerator()
    generator.generate(platform="github")

    # Check directory creation
    mock_makedirs.assert_called_with(".github/workflows", exist_ok=True)

    # Check file writing
    mock_open_func.assert_called_with(".github/workflows/deploy.yml", "w")
    # When using MagicMock for open, the context manager return value is what write is called on
    handle = mock_open_func.return_value.__enter__.return_value
    handle.write.assert_called_once()
    handle.write.assert_called_once()
    assert "vm_tool deploy-docker" in handle.write.call_args[0][0]
    assert "--host ${{ secrets.VM_HOST }}" in handle.write.call_args[0][0]
    assert "--user ${{ secrets.SSH_USER }}" in handle.write.call_args[0][0]
    assert "SSH_USER" in handle.write.call_args[0][0]  # Secret validation check
    assert "vm_tool setup-k8s" not in handle.write.call_args[0][0]
    assert (
        "vm_tool setup-monitoring" not in handle.write.call_args[0][0]
    )  # Default is False
    # Check new defaults
    content = handle.write.call_args[0][0]
    assert "python-version: '3.12'" in content
    assert "flake8" not in content
    assert "pytest" not in content
    assert "Check for Secrets" in content
    assert "Setup SSH Key" in content


def test_generate_github_pipeline_no_monitoring(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    generator = PipelineGenerator()
    generator.generate(
        platform="github", context={"branch_name": "main", "setup_monitoring": False}
    )

    handle = mock_open_func.return_value.__enter__.return_value
    handle.write.assert_called_once()
    content = handle.write.call_args[0][0]
    assert "vm_tool setup-monitoring" not in content


def test_generate_github_pipeline_custom_context(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    context = {
        "branch_name": "dev",
        "python_version": "3.10",
        "run_linting": True,
        "run_tests": True,
        "setup_monitoring": False,
    }

    generator = PipelineGenerator()
    generator.generate(platform="github", context=context)

    handle = mock_open_func.return_value.__enter__.return_value
    handle.write.assert_called_once()
    content = handle.write.call_args[0][0]

    assert "branches: [ dev ]" in content
    assert "python-version: '3.10'" in content
    assert "flake8" in content
    assert "pytest" in content
    assert "vm_tool setup-monitoring" not in content

    assert "vm_tool setup-monitoring" not in content


def test_generate_github_pipeline_docker(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    context = {
        "branch_name": "main",
        "python_version": "3.12",
        "run_linting": False,
        "run_tests": False,
        "setup_monitoring": False,
        "run_tests": False,
        "setup_monitoring": False,
        "run_tests": False,
        "setup_monitoring": False,
        "deployment_type": "docker",
        "docker_compose_file": "production.yml",
        "env_file": ".env.prod",
        "deploy_command": "./deploy.sh",
    }

    generator = PipelineGenerator()
    generator.generate(platform="github", context=context)

    handle = mock_open_func.return_value.__enter__.return_value
    handle.write.assert_called_once()
    content = handle.write.call_args[0][0]

    assert "vm_tool deploy-docker" in content
    assert "--compose-file production.yml" in content
    assert "--env-file .env.prod" in content
    assert '--deploy-command "./deploy.sh"' in content
    assert "--host ${{ secrets.VM_HOST }}" in content
    assert "SSH_USER" in content
    assert "vm_tool setup-k8s" not in content


def test_generate_github_pipeline_docker_override(mock_open_func):
    """Test generating a GitHub Actions pipeline with custom command override."""
    context = {
        "branch_name": "main",
        "python_version": "3.12",
        "run_linting": False,
        "run_tests": False,
        "setup_monitoring": False,
        "deployment_type": "docker",
        # Simulating hidden inputs holding defaults or being ignored if command is dominant
        "docker_compose_file": "docker-compose.yml",
        "env_file": None,
        "deploy_command": "make deploy",
    }

    generator = PipelineGenerator()
    generator.generate(platform="github", context=context)

    handle = mock_open_func.return_value.__enter__.return_value
    handle.write.assert_called_once()
    content = handle.write.call_args[0][0]

    assert "vm_tool deploy-docker" in content
    assert '--deploy-command "make deploy"' in content
    # It still passes compose file because it's required arg for CLI usually, or default
    assert "--compose-file docker-compose.yml" in content


def test_generate_unsupported_platform():
    generator = PipelineGenerator()
    with pytest.raises(NotImplementedError):
        generator.generate(platform="gitlab")
