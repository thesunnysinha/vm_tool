import pytest
import os
from unittest.mock import MagicMock, patch
from vm_tool.provision import Provisioner


@pytest.fixture
def mock_terraform():
    with patch("vm_tool.provision.core.Terraform") as mock:
        yield mock


def test_provisioner_init(mock_terraform):
    p = Provisioner("aws")
    mock_terraform.assert_called_once()
    assert "modules/aws" in mock_terraform.call_args[1]["working_dir"]


def test_provisioner_apply_success(mock_terraform):
    mock_instance = mock_terraform.return_value
    mock_instance.init.return_value = (0, "output", "error")
    mock_instance.apply.return_value = (0, "output", "error")

    p = Provisioner("aws")
    p.init()
    p.apply(vars={"region": "us-east-1"})

    mock_instance.init.assert_called_once()
    mock_instance.apply.assert_called_once()
    assert mock_instance.apply.call_args[1]["var"] == {"region": "us-east-1"}


def test_provisioner_apply_failure(mock_terraform):
    mock_instance = mock_terraform.return_value
    mock_instance.apply.return_value = (1, "output", "error")

    p = Provisioner("aws")

    with pytest.raises(RuntimeError):
        p.apply()
