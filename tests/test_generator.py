import os
from unittest.mock import mock_open, patch

import pytest

from vm_tool.generator import PipelineGenerator


def test_generate_github_pipeline(mock_fs):
    mock_open_func, mock_exists, mock_makedirs = mock_fs

    generator = PipelineGenerator(platform="github")
    content = generator.generate()

    # Check content
    assert "vm_tool deploy-docker" in content
    assert "EC2_HOST" in content
    assert "EC2_USER" in content
    assert "EC2_SSH_KEY" in content
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

    assert "EC2_HOST" in content
    assert "EC2_USER" in content
    assert "EC2_SSH_KEY" in content


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
    assert "EC2_HOST" in content
    assert "EC2_USER" in content
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
    assert "EC2_HOST" in content


def test_generate_unsupported_platform():
    generator = PipelineGenerator(platform="gitlab")
    with pytest.raises((NotImplementedError, ValueError)):
        generator.generate()
