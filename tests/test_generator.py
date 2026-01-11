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
    assert "vm_tool setup-k8s" in handle.write.call_args[0][0]


def test_generate_unsupported_platform():
    generator = PipelineGenerator()
    with pytest.raises(NotImplementedError):
        generator.generate(platform="gitlab")
