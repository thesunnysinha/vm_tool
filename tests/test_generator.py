import os
from unittest.mock import mock_open, patch

import pytest

from vm_tool.tools.generator import PipelineGenerator


def test_generate_github_pipeline(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    generator = PipelineGenerator(platform="github")
    content = generator.generate()

    # Check content
    assert "vm_tool deploy-docker" in content
    assert "SSH_HOSTNAME" in content
    assert "SSH_USERNAME" in content
    assert "SSH_ID_RSA" in content
    assert "Validate Required Secrets" in content
    assert "Set up SSH" in content


def test_generate_github_pipeline_no_monitoring(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    generator = PipelineGenerator(platform="github", enable_monitoring=False)
    content = generator.generate()

    assert "monitoring" not in content.lower() or "Monitoring" not in content


def test_generate_github_pipeline_custom_context(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    generator = PipelineGenerator(
        platform="github",
        enable_monitoring=False,
        enable_health_checks=True,
        enable_backup=True,
    )
    content = generator.generate()

    assert "SSH_HOSTNAME" in content
    assert "SSH_USERNAME" in content
    assert "SSH_ID_RSA" in content


def test_generate_github_pipeline_docker(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    generator = PipelineGenerator(
        platform="github",
        strategy="docker",
        enable_monitoring=False,
        enable_health_checks=True,
        enable_backup=True,
    )
    content = generator.generate()

    assert "vm_tool deploy-docker" in content
    assert "SSH_HOSTNAME" in content
    assert "SSH_USERNAME" in content
    assert "Validate Required Secrets" in content


def test_generate_github_pipeline_custom_strategy(mock_fs):
    """Test generating a GitHub Actions pipeline with 'custom' strategy."""
    mock_open_func, _, _ = mock_fs

    generator = PipelineGenerator(
        platform="github",
        strategy="custom",
        enable_monitoring=False,
    )
    content = generator.generate()

    assert "vm_tool deploy-docker" in content


def test_generate_unsupported_platform():
    generator = PipelineGenerator(platform="unsupported_xyz")
    with pytest.raises(ValueError):
        generator.generate()


def test_generate_gitlab_ci():
    generator = PipelineGenerator(platform="gitlab")
    content = generator.generate()
    assert "stages:" in content
    assert "deploy:" in content
    assert "vm_tool deploy-docker" in content
    assert "StrictHostKeyChecking=accept-new" in content
    assert "SSH_HOSTNAME" in content


def test_generate_gitlab_ci_with_options():
    generator = PipelineGenerator(
        platform="gitlab",
        enable_rollback=True,
        enable_backup=True,
        enable_health_checks=True,
    )
    generator.set_options(run_linting=True, run_tests=True)
    content = generator.generate()
    assert "lint:" in content
    assert "test:" in content
    assert "deploy:rollback" in content
    assert "health" in content.lower()
