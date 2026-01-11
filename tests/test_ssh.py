import os
from unittest.mock import MagicMock, call, patch

import pytest

from vm_tool.ssh import SSHSetup


def test_ssh_setup_init():
    ssh = SSHSetup("host", "user", "pass", "email@example.com")
    assert ssh.hostname == "host"
    assert ssh.username == "user"
    assert ssh.email == "email@example.com"


@patch("subprocess.run")
def test_ssh_setup_execution(mock_subprocess_run, mock_paramiko, mock_fs):
    mock_open, mock_exists, _ = mock_fs

    # Mock public key does not exist, so it should generate one
    mock_exists.side_effect = lambda p: not p.endswith(".pub")

    ssh = SSHSetup("host", "user", "pass", "email@example.com")

    # Mock reading public key
    mock_open.return_value.__enter__.return_value.read.return_value = "ssh-rsa AAAA..."

    ssh.setup()

    # Check key generation
    mock_subprocess_run.assert_called_with(
        [
            "ssh-keygen",
            "-t",
            "rsa",
            "-b",
            "4096",
            "-C",
            "email@example.com",
            "-f",
            os.path.expanduser("~/.ssh/id_rsa"),
            "-N",
            "",
        ],
        check=True,
        capture_output=True,
    )

    # Check SSH connection and config
    mock_client = mock_paramiko.return_value
    mock_client.connect.assert_called()
    mock_client.exec_command.assert_called_with(
        'echo "ssh-rsa AAAA..." >> ~/.ssh/authorized_keys'
    )
